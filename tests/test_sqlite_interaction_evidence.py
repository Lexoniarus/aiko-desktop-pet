"""Boundary memory and five named cursors retain original elapsed evidence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.interaction_rows import (
    read_interactions,
    write_interactions,
)
from aiko_pet.infrastructure.sqlite.moodlet_rows import write_moodlet_core
from aiko_pet.infrastructure.sqlite.pet_rows import write_pet_core
from aiko_pet.infrastructure.sqlite.poor_care_rows import (
    read_poor_care,
    write_poor_care,
)
from aiko_pet.pet.interaction_events import FoodRepetitionMemory, InteractionMemory
from aiko_pet.pet.moodlet_models import MoodletState, PoorCareCursor, PoorCareEvidence
from aiko_pet.pet.need_exposure import ExposureMark
from aiko_pet.pet.state import PetState


class SqliteInteractionEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-interaction-rows-")
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
            write_moodlet_core(connection, MoodletState(0, 10))
            connection.commit()

    def test_boundaries_and_ordered_intakes_are_separate_from_recent_food_ids(
        self,
    ) -> None:
        memory = InteractionMemory(
            100,
            200,
            90000,
            FoodRepetitionMemory(
                "apple",
                (500.123456789, 500.123456789, 900),
                False,
                1000,
                1,
            ),
            2,
            89900,
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_interactions(connection, memory)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_interactions(connection), memory)
            self.assertEqual(
                connection.execute("SELECT recent_food_ids FROM pet_state").fetchone(),
                ("[]",),
            )

    def test_unknown_and_initialized_empty_cursors_and_handled_marks_round_trip(
        self,
    ) -> None:
        empty = PoorCareEvidence(
            0, (PoorCareCursor(ExposureMark(0), ExposureMark(0)),) * 5
        )
        active = PoorCareEvidence(
            300,
            (
                PoorCareCursor(
                    ExposureMark(500, 12.3456789, 5), ExposureMark(600, 15, 7), 2, True
                ),
                *(PoorCareCursor(ExposureMark(300), ExposureMark(300)),) * 4,
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for evidence in (None, empty, active, None):
                write_poor_care(connection, evidence)
                self.assertEqual(read_poor_care(connection), evidence)
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM need_exposure_buckets"
                ).fetchone(),
                (0,),
            )

    def test_episode_core_updates_do_not_reset_independent_boundaries_or_cursors(
        self,
    ) -> None:
        memory = InteractionMemory(poke_boundary_at=10)
        evidence = PoorCareEvidence(
            0, (PoorCareCursor(ExposureMark(0), ExposureMark(0)),) * 5
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_interactions(connection, memory)
            write_poor_care(connection, evidence)
            write_moodlet_core(connection, MoodletState(0, 500))
            self.assertEqual(read_interactions(connection), memory)
            self.assertEqual(read_poor_care(connection), evidence)

    def test_missing_or_incompatible_present_evidence_is_not_defaulted(self) -> None:
        evidence = PoorCareEvidence(
            0, (PoorCareCursor(ExposureMark(0), ExposureMark(0)),) * 5
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_poor_care(connection, evidence)
            connection.execute("DELETE FROM poor_care_cursors WHERE need = 'fun'")
            with self.assertRaises(ValueError):
                read_poor_care(connection)
            write_interactions(connection, InteractionMemory())
            connection.execute("UPDATE interaction_state SET food_id = 'apple'")
            with self.assertRaises(ValueError):
                read_interactions(connection)


if __name__ == "__main__":
    unittest.main()
