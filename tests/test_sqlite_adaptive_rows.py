"""Complete anonymous profiles round-trip without rounding, sampling or learning."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from aiko_pet.infrastructure.adaptive_codec import decode_adaptive, encode_adaptive
from aiko_pet.infrastructure.sqlite.adaptive_rows import read_adaptive, write_adaptive
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.pet.mind.adaptive_models import SLOTS, AdaptiveMemory
from aiko_pet.pet.mind.quiet_rhythm import QuietPhase, QuietWindow


def profile() -> AdaptiveMemory:
    return AdaptiveMemory(
        hour_seconds=[10.123456789 + i / 10000 for i in range(SLOTS)],
        busy_seconds=[4.123456789] * SLOTS,
        present_seconds=[9.123456789] * SLOTS,
        observed_days=[0.123456789] * SLOTS,
        last_slot_key="2026-10-24T15",
        profile_day="2026-10-24",
        strain=23.123456789,
        settled_work=0.123456789,
        session_seconds=7200.123456789,
        rest_seconds=100.123456789,
        last_session_seconds=3600.123456789,
        last_work_wall=1780000000.1234567,
        last_contact_wall=1780000001.1234567,
        last_seen_wall=1780000002.1234567,
        quiet_window=QuietWindow(
            1380.123456789,
            420.23456789,
            (
                QuietPhase("2026-10-21", 1380.123456789, 420.23456789),
                QuietPhase("2026-10-22", 1390.123456789, 430.23456789),
            ),
            "2026-10-22",
        ),
    )


class SqliteAdaptiveRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-adaptive-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        with open_database(self.path, initialize=True) as connection:
            connection.execute(
                "INSERT INTO save_state VALUES (1, 1, 1800000000, 90000)"
            )

    def test_all_slots_fractional_days_and_cross_midnight_phases_keep_precision(
        self,
    ) -> None:
        original = profile()
        captured = copy.deepcopy(original)
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_adaptive(connection, original)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_adaptive(connection), captured)
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM adaptive_hour_slots"
                ).fetchone(),
                (168,),
            )
            self.assertEqual(
                connection.execute("SELECT lived_seconds FROM save_state").fetchone(),
                (90000,),
            )
        self.assertEqual(original, captured)

    def test_neutral_profile_replaces_old_data_without_retaining_old_phases(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_adaptive(connection, profile())
            write_adaptive(connection, AdaptiveMemory())
            self.assertEqual(read_adaptive(connection), AdaptiveMemory())
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM adaptive_quiet_phases"
                ).fetchone(),
                (0,),
            )

    def test_invalid_present_values_cannot_be_normalized_or_replace_saved_data(
        self,
    ) -> None:
        original = profile()
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_adaptive(connection, original)
            for mutate in (
                lambda raw: raw["hour_seconds"].__setitem__(0, True),
                lambda raw: raw.update(strain=101),
                lambda raw: raw.update(rest_seconds=float("nan")),
                lambda raw: raw["quiet_window"].update(version=True),
            ):
                raw = encode_adaptive(original)
                mutate(raw)
                with self.assertRaises(ValueError):
                    decode_adaptive(raw)
            invalid = copy.deepcopy(original)
            invalid.hour_seconds = [0.0]
            with self.assertRaises(ValueError):
                write_adaptive(connection, invalid)
            self.assertEqual(read_adaptive(connection), original)

    def test_missing_slot_or_bad_scalar_is_rejected_instead_of_starting_new_history(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            with self.assertRaises(ValueError):
                read_adaptive(connection)
            for statement in (
                "DELETE FROM adaptive_hour_slots WHERE slot = 0",
                "UPDATE adaptive_state SET strain = 101",
            ):
                write_adaptive(connection, profile())
                connection.execute(statement)
                with self.assertRaises(ValueError):
                    read_adaptive(connection)


if __name__ == "__main__":
    unittest.main()
