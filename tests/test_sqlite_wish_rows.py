"""Frozen goals, expired pins and bounded cumulative evidence survive SQL reads."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.pet_rows import write_pet_core
from aiko_pet.infrastructure.sqlite.wish_rows import read_wish_core, write_wish_core
from aiko_pet.pet.food_handover import FoodHandoverReceipt
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishGoal,
    WishId,
    WishObjective,
    WishState,
)


def flexible_wishes() -> WishState:
    active = []
    for index, (instance, key, reference) in enumerate(
        (
            (2, WishId.PLAY_GAME, "mastermind"),
            (5, WishId.PLAY_ANY_GAME, None),
            (3, WishId.PLAY_OTHER_GAME, "blackjack"),
        ),
        start=1,
    ):
        definition = WISH_CATALOG.definitions[key]
        start = index * 100
        active.append(
            ActiveWish(
                instance,
                key,
                reference or "",
                start,
                start + 14400,
                expressed_at=150 if index == 1 else None,
                goal=definition.goal,
                pinned=index == 1,
                target=definition.bind_target(reference),
            )
        )
    return WishState(
        500,
        tuple(active),
        ((WishArea.GAMES, 300),),
        last_expressed_at=150,
        refresh_at=1200,
    )


class SqliteWishRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-wish-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        with open_database(self.path, initialize=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO save_state VALUES (1, 1, 1780000000, 100000)"
            )
            write_pet_core(
                connection,
                PetState(
                    updated_at=1780000000,
                    lived_seconds=100000,
                ).capture_checkpoint(),
            )
            connection.commit()

    def test_exact_free_excluded_and_expired_pinned_wishes_keep_original_order(
        self,
    ) -> None:
        original = flexible_wishes()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wish_core(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_wish_core(connection), original)
            self.assertEqual(
                connection.execute(
                    "SELECT target_mode, target_id FROM wish_instances "
                    "ORDER BY position_index"
                ).fetchall(),
                [("exact", "mastermind"), ("any", None), ("exclude", "blackjack")],
            )
            self.assertEqual(
                connection.execute("SELECT lived_seconds FROM save_state").fetchone(),
                (100000,),
            )

    def test_legacy_target_session_goal_and_individual_expiry_are_not_rewritten(
        self,
    ) -> None:
        original = WishState(
            2,
            (
                ActiveWish(
                    1,
                    WishId.PLAY_GAME,
                    "blackjack",
                    10,
                    14410,
                    game=GameWishProgress(("session-A:1",), 1, 0, "session-A", 1),
                    goal=WishGoal(WishObjective.SESSION_ROUNDS, 5),
                    pinned=True,
                ),
            ),
            ((WishArea.GAMES, 10),),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wish_core(connection, original)
            self.assertEqual(read_wish_core(connection), original)
            self.assertEqual(
                connection.execute(
                    "SELECT target_explicit, target_kind, target_mode "
                    "FROM wish_instances"
                ).fetchone(),
                (0, None, None),
            )

    def test_pinned_cumulative_counts_are_independent_of_bounded_round_receipts(
        self,
    ) -> None:
        goal = WishGoal(WishObjective.TOTAL_WINS, 4)
        original = WishState(
            200,
            (
                ActiveWish(
                    7,
                    WishId.WIN_OVERALL,
                    "connect_four",
                    10,
                    14410,
                    game=GameWishProgress(
                        ("recent-session:round-4",), 1, 49999, completed_rounds=50000
                    ),
                    goal=goal,
                    pinned=True,
                    target=WISH_CATALOG.definitions[WishId.WIN_OVERALL].bind_target(
                        "connect_four"
                    ),
                ),
            ),
            ((WishArea.GAMES, 10),),
            refresh_at=1200,
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wish_core(connection, original)
            restored = read_wish_core(connection)
            self.assertEqual(restored, original)
            self.assertEqual(restored.active[0].game.completed_rounds, 50000)
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM wish_round_receipts"
                ).fetchone(),
                (1,),
            )
            retired = replace(original, active=())
            write_wish_core(connection, retired)
            self.assertEqual(read_wish_core(connection), retired)
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM wish_round_receipts"
                ).fetchone(),
                (0,),
            )

    def test_core_read_preserves_the_separate_handover_template(self) -> None:
        original = flexible_wishes()
        template = WishState(
            food_handovers=(
                FoodHandoverReceipt(
                    "original-offer",
                    "object_9",
                    500,
                ),
            )
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wish_core(connection, original)
            self.assertEqual(
                read_wish_core(connection, template),
                replace(original, food_handovers=template.food_handovers),
            )

    def test_incompatible_present_goal_and_area_are_rejected_without_defaults(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for statement in (
                "UPDATE wish_instances SET required_count = 0 WHERE instance_id = 2",
                "UPDATE wish_instances SET area = 'food' WHERE instance_id = 2",
            ):
                write_wish_core(connection, flexible_wishes())
                connection.execute(statement)
                with self.assertRaises(ValueError):
                    read_wish_core(connection)

    def test_transaction_and_valid_input_are_required_before_replacing_rows(
        self,
    ) -> None:
        original = flexible_wishes()
        with open_database(self.path) as connection:
            with self.assertRaises(ValueError):
                write_wish_core(connection, original)
            connection.execute("BEGIN IMMEDIATE")
            write_wish_core(connection, original)
            with self.assertRaises(ValueError):
                write_wish_core(connection, replace(original, next_instance_id=2))
            self.assertEqual(read_wish_core(connection), original)


if __name__ == "__main__":
    unittest.main()
