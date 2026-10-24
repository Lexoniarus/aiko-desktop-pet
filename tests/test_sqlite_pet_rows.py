"""Core SQL round trips preserve exact values without advancing the pet."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.pet_rows import read_pet_core, write_pet_core
from aiko_pet.infrastructure.sqlite.settings_rows import read_settings, write_settings
from aiko_pet.pet.food import FoodState
from aiko_pet.pet.sleep import SleepEpisode
from aiko_pet.pet.state import PetState


class SqlitePetRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-pet-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        self.snapshot = PetState(
            satiety=43.123456789, energy=21, fun=39, social=87, affection=0,
            mood=12, friendship=56.23456789, updated_at=1780000000,
            lived_seconds=7200, friendship_day="2026-10-24",
            friendship_gained_today=1.23456789, care_types_today=["talk", "pet"],
            care_last_rewards={"sleep": 1779999000.12345}, sleeping=True,
            meals_date="2026-10-24", meals_today=["breakfast", "lunch"],
            sleep_origin="manual", auto_sleep_night="2026-10-23",
            nap_until=1780000900, auto_nap_day="2026-10-24",
            food=FoodState(31.123456789, 3.345678901, 9.87654321, ("apple", "apple")),
            sleep_episode=SleepEpisode("main", 3600, 900, 1780010000, 7201,
                                       True, 7202, 7203, True, ("object_7",)),
        ).capture_checkpoint()
        with open_database(self.path, initialize=True) as connection:
            connection.execute("INSERT INTO save_state VALUES (1, 1, ?, ?)",
                               (self.snapshot.updated_at, self.snapshot.lived_seconds))

    def test_exact_core_sleep_and_time_round_trip_keeps_other_owners(self) -> None:
        template = replace(PetState(updated_at=1).capture_checkpoint(),
                           relationship=self.snapshot.relationship,
                           moodlets=self.snapshot.moodlets, wishes=self.snapshot.wishes)
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_pet_core(connection, self.snapshot)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            restored = read_pet_core(connection, template)
            self.assertEqual(restored, self.snapshot)
        self.assertEqual(self.snapshot.food.recent_food_ids, ("apple", "apple"))

    def test_repeated_write_keeps_unrelated_owned_rows(self) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_pet_core(connection, self.snapshot)
            connection.execute("CREATE TABLE fixture_link (pet_id INTEGER "
                               "REFERENCES pet_state(id) ON DELETE CASCADE)")
            connection.execute("INSERT INTO fixture_link VALUES (1)")
            newer = replace(self.snapshot, mood=22)
            write_pet_core(connection, newer)
            self.assertEqual(read_pet_core(connection, self.snapshot), newer)
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM fixture_link"
            ).fetchone(), (1,))

    def test_transaction_and_checkpoint_are_required_before_mapping(self) -> None:
        with open_database(self.path) as connection:
            with self.assertRaises(ValueError):
                write_pet_core(connection, self.snapshot)
            connection.execute("BEGIN IMMEDIATE")
            with self.assertRaises(ValueError):
                write_pet_core(connection, replace(self.snapshot, lived_seconds=0))
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM pet_state"
            ).fetchone(), (0,))

    def test_missing_sleep_or_invalid_history_is_rejected_instead_of_defaulted(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_pet_core(connection, self.snapshot)
            connection.execute("UPDATE pet_state SET recent_food_ids = '[\"unknown\"]'")
            with self.assertRaises(ValueError):
                read_pet_core(connection, self.snapshot)
            write_pet_core(connection, self.snapshot)
            connection.execute("DELETE FROM sleep_state")
            with self.assertRaises(ValueError):
                read_pet_core(connection, self.snapshot)

    def test_settings_round_trip_and_invalid_values_do_not_silently_reset(self) -> None:
        settings = PetSettings(
            x=-500, y=73, scale=2, toolbar_x=0, toolbar_y=-100,
            always_on_top=False, auto_walk=False, auto_routine=False,
            follow_cursor=False, spontaneous_talk=False, observe_computer=False,
            learn_rhythm=False, online_social=True,
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_settings(connection, settings)
            self.assertEqual(read_settings(connection), settings)
            connection.execute("UPDATE app_settings SET x = 20001")
            with self.assertRaises(ValueError):
                read_settings(connection)


if __name__ == "__main__":
    unittest.main()
