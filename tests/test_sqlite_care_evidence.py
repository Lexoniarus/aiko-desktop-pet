"""Complete emotional snapshots retain qualified facts without replay or clocks."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from test_care_evidence_storage import emotional_state

from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.infrastructure.sqlite.care_evidence_rows import read_care_evidence
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.moodlet_rows import (
    read_moodlets,
    write_moodlet_core,
    write_moodlets,
)
from aiko_pet.infrastructure.sqlite.pet_rows import write_pet_core
from aiko_pet.pet.care_evidence import (
    CareActivity,
    CareEvidenceState,
    CareExperience,
    LongTermProgress,
)
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlet_models import MoodletState, PoorCareCursor, PoorCareEvidence
from aiko_pet.pet.moodlets import MoodletGroup, MoodletOutcome
from aiko_pet.pet.need_exposure import ExposureMark
from aiko_pet.pet.state import PetState


def complete_emotional_state() -> MoodletState:
    source = emotional_state()
    assert source.care_evidence is not None
    evidence = replace(
        source.care_evidence,
        next_encounter_id=200,
        next_experience_id=900,
        progress=tuple(
            LongTermProgress(definition.id, 86400, 86400, 90000, 123.5, 500.25)
            for definition in MOODLET_CATALOG.definitions.values()
            if definition.group == MoodletGroup.LONG_TERM
        ),
        experiences=(
            *source.care_evidence.experiences,
            CareExperience(
                "withheld:1",
                88000,
                CareActivity.WITHHOLDING,
                MoodletOutcome.COMPLETED,
                upsetting=True,
                boundary_violated=True,
                object_id="object_99",
            ),
        ),
    )
    mark = ExposureMark(100, 30, 10)
    poor = PoorCareEvidence(0, (PoorCareCursor(mark, mark),) * 5)
    return replace(source, care_evidence=evidence, poor_care=poor)


class SqliteCareEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-care-rows-")
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

    def test_complete_snapshot_flags_and_all_six_processing_families_round_trip(
        self,
    ) -> None:
        original = complete_emotional_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlets(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_moodlets(connection), original)
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM long_term_progress"
                ).fetchone(),
                (6,),
            )
            self.assertEqual(
                connection.execute(
                    "SELECT pleasant, upsetting, boundary_violated, "
                    "encounter_id, object_id "
                    "FROM care_evidence WHERE receipt_id = 'withheld:1'"
                ).fetchone(),
                (0, 1, 1, None, "object_99"),
            )
            self.assertEqual(
                connection.execute("SELECT lived_seconds FROM save_state").fetchone(),
                (90000,),
            )

    def test_unknown_empty_and_pruned_allocation_metadata_stay_distinct(self) -> None:
        empty = CareEvidenceState(0, next_encounter_id=200, next_experience_id=900)
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for evidence in (None, empty, None):
                original = MoodletState(care_evidence=evidence)
                write_moodlets(connection, original)
                self.assertEqual(read_moodlets(connection), original)
            write_moodlets(connection, MoodletState(care_evidence=empty))
            write_moodlet_core(connection, MoodletState(next_instance_id=500))
            self.assertEqual(read_care_evidence(connection), empty)

    def test_pruning_raw_rows_keeps_period_causes_processing_and_identity_counters(
        self,
    ) -> None:
        original = complete_emotional_state()
        assert original.care_evidence is not None
        pruned = replace(
            original,
            care_evidence=replace(
                original.care_evidence,
                encounters=(),
                experiences=(),
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlets(connection, original)
            write_moodlets(connection, pruned)
            self.assertEqual(read_moodlets(connection), pruned)
            self.assertEqual(
                connection.execute(
                    "SELECT next_encounter_id, next_experience_id FROM moodlet_state"
                ).fetchone(),
                (200, 900),
            )
            self.assertEqual(
                connection.execute("SELECT count(*) FROM care_evidence").fetchone(),
                (0,),
            )

    def test_retained_semantic_receipts_protect_their_actual_encounter(self) -> None:
        original = complete_emotional_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlets(connection, original)
            connection.commit()
        with self.assertRaises(StorageError):
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("DELETE FROM care_encounters WHERE instance_id = 1")
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_moodlets(connection), original)

    def test_invalid_input_and_inconsistent_present_history_do_not_default(
        self,
    ) -> None:
        original = complete_emotional_state()
        assert original.care_evidence is not None
        invalid = replace(
            original,
            care_evidence=replace(
                original.care_evidence,
                experiences=(
                    replace(
                        original.care_evidence.experiences[0],
                        upsetting=True,
                    ),
                ),
            ),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlets(connection, original)
            with self.assertRaises(ValueError):
                write_moodlets(connection, invalid)
            self.assertEqual(read_moodlets(connection), original)
            connection.execute(
                "UPDATE long_term_progress SET definition_id = 'pride' "
                "WHERE position_index = 0"
            )
            with self.assertRaises(ValueError):
                read_moodlets(connection)
            write_moodlets(connection, original)
            connection.execute(
                "UPDATE moodlet_state SET care_evidence_baseline = NULL, "
                "next_encounter_id = NULL, next_experience_id = NULL"
            )
            with self.assertRaises(ValueError):
                read_moodlets(connection)

    def test_later_failure_restores_all_moodlet_parts_and_the_saved_time_revision(
        self,
    ) -> None:
        original = complete_emotional_state()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_moodlets(connection, original)
            connection.commit()
        with self.assertRaises(StorageError):
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE save_state SET revision = 2, "
                    "lived_seconds = 90030, updated_at = 1800000030"
                )
                write_moodlets(connection, MoodletState())
                connection.execute("UPDATE pet_state SET mood = -1")
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_moodlets(connection), original)
            self.assertEqual(
                connection.execute(
                    "SELECT revision, lived_seconds FROM save_state"
                ).fetchone(),
                (1, 90000),
            )


if __name__ == "__main__":
    unittest.main()
