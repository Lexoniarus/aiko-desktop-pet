"""Original transfer facts survive wish retirement and delayed recognition."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.pet_rows import write_pet_core
from aiko_pet.infrastructure.sqlite.wish_rows import (
    read_wishes,
    write_wish_core,
    write_wishes,
)
from aiko_pet.pet.food_handover import (
    FoodHandoverReceipt,
    FoodWishSnapshot,
    HandoverStatus,
)
from aiko_pet.pet.food_wishes import recognize_food_handover
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState


def handover_state() -> WishState:
    desired, excluded = (
        WISH_CATALOG.definitions[key] for key in (WishId.FOOD, WishId.AVOID_FOOD)
    )
    context = (
        FoodWishSnapshot(
            10, desired.id, desired.bind_target("apple"), desired.goal, 100, 200, True
        ),
        FoodWishSnapshot(
            11, excluded.id, excluded.bind_target("donut"), excluded.goal, 110
        ),
    )
    return WishState(
        30,
        last_created_by_area=((WishArea.FOOD, 110),),
        last_expressed_at=200,
        refresh_at=1200,
        food_handovers=(
            FoodHandoverReceipt("offer:first", "object_99", 500.125, context),
            FoodHandoverReceipt("offer:second", "object_100", 600.375, context[:1]),
        ),
    )


class SqliteFoodHandoverTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-handover-rows-")
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

    def test_complete_round_trip_neither_identifies_food_nor_requires_live_stock(
        self,
    ) -> None:
        original = handover_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_wishes(connection), original)
            self.assertEqual(
                connection.execute("SELECT count(*) FROM world_objects").fetchone(),
                (0,),
            )
            self.assertEqual(
                connection.execute(
                    "SELECT recognized_at FROM food_handover_receipts "
                    "ORDER BY position_index"
                ).fetchall(),
                [(None,), (None,)],
            )

    def test_core_rotation_and_active_wish_deletion_preserve_original_context(
        self,
    ) -> None:
        original = handover_state()
        requested = original.food_handovers[0].wishes[0]
        original = replace(
            original,
            active=(
                ActiveWish(
                    requested.instance_id,
                    requested.definition_id,
                    requested.target.target_id or "",
                    requested.created_at,
                    14500,
                    expressed_at=requested.expressed_at,
                    goal=requested.goal,
                    pinned=requested.pinned,
                    target=requested.target,
                ),
            ),
        )
        game = WISH_CATALOG.definitions[WishId.PLAY_GAME]
        later = replace(
            original,
            active=(
                ActiveWish(
                    20,
                    game.id,
                    "mastermind",
                    1000,
                    1600,
                    goal=game.goal,
                    target=game.bind_target("mastermind"),
                ),
            ),
            last_created_by_area=(
                *original.last_created_by_area,
                (WishArea.GAMES, 1000),
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(connection, original)
            write_wish_core(connection, later)
            self.assertEqual(read_wishes(connection), later)
            connection.execute("DELETE FROM wish_instances")
            self.assertEqual(read_wishes(connection), replace(later, active=()))

    def test_recognition_after_reload_settles_original_wish_only_once(self) -> None:
        original = handover_state()
        original = replace(
            original,
            food_handovers=tuple(
                replace(receipt, wishes=receipt.wishes[:1])
                for receipt in original.food_handovers
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            loaded = read_wishes(connection)
            result = recognize_food_handover(
                loaded,
                handover_id="offer:first",
                food_id="apple",
                elapsed=100000,
                definitions=WISH_CATALOG.definitions,
            )
            assert result.cause is not None and result.cause.wish is not None
            self.assertEqual(result.cause.wish.instance_id, 10)
            self.assertEqual(
                (result.cause.handed_over_at, result.cause.occurred_at),
                (500.125, 100000),
            )
            write_wishes(connection, result.state)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            loaded = read_wishes(connection)
            self.assertEqual(loaded.food_handovers[0].resolved_wish_instance_id, 10)
            self.assertEqual(loaded.food_handovers[1].accounted_wish_ids, (10,))
            for handover_id in ("offer:first", "offer:second"):
                repeated = recognize_food_handover(
                    loaded,
                    handover_id=handover_id,
                    food_id="apple",
                    elapsed=100000,
                    definitions=WISH_CATALOG.definitions,
                )
                self.assertIsNone(repeated.cause)
                self.assertIsNone(repeated.fulfilled)

    def test_unwanted_food_result_and_cancelled_receipt_keep_distinct_facts(
        self,
    ) -> None:
        original = handover_state()
        result = recognize_food_handover(
            original,
            handover_id="offer:first",
            food_id="donut",
            elapsed=100000,
            definitions=WISH_CATALOG.definitions,
        )
        assert result.cause is not None and result.cause.wish is not None
        self.assertIsNone(result.fulfilled)
        self.assertEqual(result.cause.wish.instance_id, 11)
        cancelled = replace(
            result.state.food_handovers[1], status=HandoverStatus.CANCELLED
        )
        expected = replace(
            result.state,
            food_handovers=(
                result.state.food_handovers[0],
                cancelled,
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(connection, expected)
            self.assertEqual(read_wishes(connection), expected)

    def test_bad_context_accounting_and_duplicate_pending_input_do_not_reset_data(
        self,
    ) -> None:
        original = handover_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for statement in (
                "UPDATE food_handover_receipts SET "
                'wish_context = \'{"version":2,"wishes":[]}\'',
                "UPDATE food_handover_receipts SET accounted_wish_ids = '[999]'",
            ):
                write_wishes(connection, original)
                connection.execute(statement)
                with self.assertRaises(ValueError):
                    read_wishes(connection)
            write_wishes(connection, original)
            duplicate = replace(
                original.food_handovers[0], handover_id="different-offer"
            )
            with self.assertRaises(ValueError):
                write_wishes(
                    connection,
                    replace(
                        original,
                        food_handovers=(
                            original.food_handovers[0],
                            duplicate,
                        ),
                    ),
                )
            self.assertEqual(read_wishes(connection), original)

    def test_database_enforces_one_open_handover_per_object(self) -> None:
        original = handover_state()
        pending = original.food_handovers[0]
        cancelled = replace(
            pending, handover_id="cancelled", status=HandoverStatus.CANCELLED
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(
                connection, replace(original, food_handovers=(cancelled, pending))
            )
            connection.commit()
        with self.assertRaises(StorageError):
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO food_handover_receipts SELECT 'duplicate', state_id, "
                    "99, object_id, handed_over_at, wish_context, recognized_food_id, "
                    "recognized_at, status, resolved_wish_instance_id, "
                    "accounted_wish_ids "
                    "FROM food_handover_receipts WHERE status = 'pending'"
                )

    def test_later_failure_rolls_back_wishes_and_handover_changes_together(
        self,
    ) -> None:
        original = handover_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(connection, original)
            connection.commit()
        with self.assertRaises(StorageError):
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                write_wishes(
                    connection,
                    replace(original, food_handovers=(), next_instance_id=40),
                )
                connection.execute("UPDATE pet_state SET mood = -1")
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_wishes(connection), original)


if __name__ == "__main__":
    unittest.main()
