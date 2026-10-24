"""Reuse canonical emotional fixtures to verify SQL stages and actual causes."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_care_evidence_storage import emotional_state
from test_emotional_persistence import moodlet_state

from aiko_pet.application.storage_contracts import StorageError, StorageFailureKind
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.moodlet_rows import (
    read_moodlet_core,
    write_moodlet_core,
)
from aiko_pet.infrastructure.sqlite.pet_rows import write_pet_core
from aiko_pet.infrastructure.sqlite.wish_rows import write_wishes
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    WishArea,
    WishGoal,
    WishId,
    WishObjective,
    WishState,
)


class SqliteMoodletRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-moodlet-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        with open_database(self.path, initialize=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO save_state VALUES (1, 1, 1800000000, 90000)"
            )
            write_pet_core(
                connection,
                PetState(
                    updated_at=1800000000,
                    lived_seconds=90000,
                ).capture_checkpoint(),
            )
            connection.commit()

    def test_actual_wish_game_food_and_period_causes_round_trip_without_progression(
        self,
    ) -> None:
        original = emotional_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlet_core(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_moodlet_core(connection, original), original)
            self.assertEqual(
                connection.execute("SELECT lived_seconds FROM save_state").fetchone(),
                (90000,),
            )

    def test_implicit_and_zero_budgets_and_relief_above_current_level_remain_distinct(
        self,
    ) -> None:
        source = moodlet_state()
        source = replace(
            source,
            active=(
                replace(source.active[0], level=1, relieved_levels=(3, 1)),
                *source.active[1:],
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for lower in ((), (0.0,)):
                original = replace(
                    source,
                    active=(
                        *source.active[:-1],
                        replace(source.active[-1], lower_stage_seconds=lower),
                    ),
                )
                write_moodlet_core(connection, original)
                self.assertEqual(read_moodlet_core(connection), original)
                self.assertEqual(
                    connection.execute(
                        "SELECT stage FROM moodlet_stage_state WHERE episode_id = 1 "
                        "ORDER BY relief_position"
                    ).fetchall(),
                    [(3,), (1,)],
                )

    def test_semantic_receipts_allow_distinct_original_wishes_on_the_same_event(
        self,
    ) -> None:
        causes = tuple(
            MoodletCause(
                MoodletCauseKind.WISH_FULFILLED,
                100,
                "same-round",
                wish=MoodletWishCause(
                    instance, "win_overall", "blackjack", "total_wins", 3
                ),
                target_id="blackjack",
                outcome=MoodletOutcome.WIN,
            )
            for instance in (1, 2, 3)
        )
        original = MoodletState(
            0,
            2,
            (
                MoodletEpisode(
                    1,
                    MoodletId.PRIDE,
                    3,
                    100,
                    100,
                    3600,
                    causes=causes,
                    lower_stage_seconds=(4200, 2700),
                ),
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlet_core(connection, original)
            self.assertEqual(read_moodlet_core(connection), original)
            weaker = replace(
                original,
                active=(
                    replace(original.active[0], level=2, lower_stage_seconds=(4200,)),
                ),
            )
            write_moodlet_core(connection, weaker)
            self.assertEqual(read_moodlet_core(connection), weaker)
            self.assertEqual(
                connection.execute(
                    "SELECT source_wish_instance_id FROM moodlet_causes "
                    "ORDER BY position_index"
                ).fetchall(),
                [(2,), (3,)],
            )

    def test_null_wish_receipts_cannot_be_duplicated_in_the_same_episode(self) -> None:
        cause = MoodletCause(MoodletCauseKind.INTERACTION, 100, "click:1")
        original = MoodletState(
            0,
            2,
            (
                MoodletEpisode(
                    1,
                    MoodletId.POKING,
                    2,
                    100,
                    100,
                    600,
                    causes=(cause,),
                ),
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlet_core(connection, original)
            connection.commit()
        with self.assertRaises(StorageError) as failure:
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT INTO moodlet_causes(episode_id, position_index, kind, "
                    "occurred_at, event_id, attribution, target_id, outcome, "
                    "object_id, handed_over_at, source_wish_instance_id, "
                    "wish_snapshot, details_snapshot) "
                    "SELECT episode_id, 1, kind, occurred_at, event_id, attribution, "
                    "target_id, "
                    "outcome, object_id, handed_over_at, source_wish_instance_id, "
                    "wish_snapshot, details_snapshot FROM moodlet_causes"
                )
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATA)

    def test_wish_retirement_keeps_causes_and_episode_end_cleans_only_owned_rows(
        self,
    ) -> None:
        original = emotional_state()
        definition = WISH_CATALOG.definitions[WishId.PLAY_ANY_GAME]
        wishes = WishState(
            8,
            (
                ActiveWish(
                    7,
                    definition.id,
                    "",
                    80000,
                    94400,
                    goal=WishGoal(WishObjective.TOTAL_ROUNDS, 2),
                    target=definition.bind_target(),
                ),
            ),
            ((WishArea.GAMES, 80000),),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_wishes(connection, wishes)
            write_moodlet_core(connection, original)
            connection.execute("DELETE FROM wish_instances")
            self.assertEqual(read_moodlet_core(connection, original), original)
            write_moodlet_core(connection, replace(original, active=()))
            for table in ("moodlet_episodes", "moodlet_stage_state", "moodlet_causes"):
                self.assertEqual(
                    connection.execute(f"SELECT count(*) FROM {table}").fetchone(), (0,)
                )
            self.assertEqual(
                connection.execute(
                    "SELECT next_instance_id FROM wish_state"
                ).fetchone(),
                (8,),
            )

    def test_missing_causes_budgets_and_unknown_detail_versions_do_not_default(
        self,
    ) -> None:
        original = emotional_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for statement in (
                "DELETE FROM moodlet_causes WHERE episode_id = 1",
                "DELETE FROM moodlet_stage_state "
                "WHERE lower_remaining_seconds IS NOT NULL",
                "UPDATE moodlet_causes SET details_snapshot = "
                "'{\"version\":2,\"game\":null,\"period\":null}'",
            ):
                write_moodlet_core(connection, original)
                connection.execute(statement)
                with self.assertRaises(ValueError):
                    read_moodlet_core(connection)


if __name__ == "__main__":
    unittest.main()
