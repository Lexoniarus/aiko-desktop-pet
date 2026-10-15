"""Closed-session time advances once, without fabricated human care or work."""

from __future__ import annotations

import tempfile
import unittest
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.state import PetState


def local_stamp(hour: int, *, day: int = 12) -> float:
    return datetime(2026, 10, day, hour).astimezone().timestamp()


class OfflineProgressTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="aiko-offline-test-")
        self.addCleanup(temporary.cleanup)
        self.store = StateStore(Path(temporary.name) / "state.json")

    def test_saved_hour_and_next_live_minute_are_consumed_once(self) -> None:
        now = local_stamp(15)
        self.store.save(
            PetState(satiety=100, energy=100, updated_at=now - 3600),
            PetSettings(auto_routine=False),
        )
        session = PetSessionRestorer(self.store, wall_time=lambda: now).restore()
        self.assertAlmostEqual(session.state.satiety, 92)
        uptime = [5000.0]
        clock = ActiveSessionClock(lambda: uptime[0])
        # Starting the live clock cannot consume the closed hour again.
        session.state.advance(now, elapsed_seconds=clock.consume())
        self.assertAlmostEqual(session.state.energy, 94)
        uptime[0] += 60
        session.state.advance(now + 60, elapsed_seconds=clock.consume())
        self.assertAlmostEqual(session.state.energy, 93.9)
        session.state.advance(now + 60, elapsed_seconds=clock.consume())
        self.assertAlmostEqual(session.state.energy, 93.9)

    def test_offline_routine_sleeps_at_night_and_recovers_energy(self) -> None:
        now = local_stamp(7, day=13)
        self.store.save(
            PetState(energy=20, updated_at=local_stamp(23)),
            PetSettings(auto_routine=True),
        )
        session = PetSessionRestorer(self.store, wall_time=lambda: now).restore()
        self.assertTrue(session.state.sleeping)
        self.assertEqual(session.state.sleep_origin, "routine")
        self.assertEqual(session.state.energy, 100)
        self.assertLess(session.state.satiety, 75)
        self.assertEqual(session.state.friendship, 15)

    def test_offline_breakfast_is_nutrition_without_human_care_rewards(self) -> None:
        now = local_stamp(10)
        saved = PetState(
            satiety=20,
            energy=30,
            friendship=40,
            updated_at=local_stamp(7),
            care_types_today=["pet"],
            care_last_rewards={"pet": local_stamp(6)},
        )
        memory = AdaptiveMemory()
        memory.hour_seconds[42] = 60
        self.store.save(saved, PetSettings(auto_routine=True), adaptive=memory)
        original = self.store.path.read_bytes()
        session = PetSessionRestorer(self.store, wall_time=lambda: now).restore()
        self.assertIn("breakfast", session.state.meals_today)
        self.assertIsNotNone(session.state.food.last_food_id)
        self.assertGreater(session.state.satiety, 20)
        self.assertFalse(session.state.sleeping)
        self.assertEqual(session.state.friendship, 40)
        self.assertEqual(session.state.care_types_today, ["pet"])
        self.assertEqual(session.state.care_last_rewards, saved.care_last_rewards)
        self.assertEqual(session.adaptive.memory.hour_seconds, memory.hour_seconds)
        # Reading/restoration itself does not write to the user's repository.
        self.assertEqual(self.store.path.read_bytes(), original)

    def test_disabled_routine_and_live_ticks_do_not_invent_meals(self) -> None:
        start, end = local_stamp(8), local_stamp(9)
        self.store.save(
            PetState(satiety=20, updated_at=start),
            PetSettings(auto_routine=False),
        )
        restored = PetSessionRestorer(self.store, wall_time=lambda: end).restore()
        self.assertEqual(restored.state.meals_today, [])
        self.assertIsNone(restored.state.food.last_food_id)
        live = PetState(satiety=20, updated_at=start)
        live.advance(end, auto_routine=True, elapsed_seconds=3600)
        self.assertEqual(live.meals_today, [])
        self.assertIsNone(live.food.last_food_id)

    def test_long_absence_is_bounded_and_backward_clock_does_not_decay(self) -> None:
        now = local_stamp(15)
        for age, expected_energy in ((30 * 86400, 52), (-3600, 100)):
            with self.subTest(age=age):
                self.store.save(
                    PetState(energy=100, updated_at=now - age),
                    PetSettings(auto_routine=False),
                )
                result = PetSessionRestorer(self.store, wall_time=lambda: now).restore()
                self.assertAlmostEqual(result.state.energy, expected_energy)
                self.assertEqual(result.state.updated_at, now)

    def test_saving_and_restarting_does_not_repeat_the_closed_interval(self) -> None:
        now = local_stamp(15)
        self.store.save(
            PetState(satiety=100, updated_at=now - 3600),
            PetSettings(auto_routine=False),
        )
        first = PetSessionRestorer(self.store, wall_time=lambda: now).restore()
        self.store.save(first.state, first.settings, adaptive=first.adaptive.memory)
        second = PetSessionRestorer(self.store, wall_time=lambda: now).restore()
        self.assertEqual(encode_pet_state(second.state), encode_pet_state(first.state))
        self.assertAlmostEqual(second.state.satiety, 92)

    def test_unreadable_and_future_saves_are_backed_up_before_replacement(self) -> None:
        for contents in (b"{broken", b'{"version": 99, "future": "preserve"}', b"\xff"):
            with self.subTest(contents=contents):
                self.store.path.write_bytes(contents)
                self.store.save(PetState(updated_at=local_stamp(15)), PetSettings())
                backups = list(self.store.path.parent.glob("*.aiko-save-backup"))
                self.assertIn(contents, [file.read_bytes() for file in backups])
                self.assertEqual(self.store.load_session().state.satiety, 75)

    def test_failed_backup_preserves_original_and_existing_backup(self) -> None:
        contents = b'{"version": 99, "future": "preserve"}'
        self.store.path.write_bytes(contents)
        identity = uuid.UUID(int=0)
        backup = self.store.path.with_name(
            f"{self.store.path.stem}-{identity.hex}.aiko-save-backup"
        )
        backup.write_bytes(b"earlier backup")
        with patch(
            "aiko_pet.infrastructure.persistence.uuid.uuid4", return_value=identity
        ):
            with self.assertRaises(FileExistsError):
                self.store.save(PetState(), PetSettings())
        self.assertEqual(self.store.path.read_bytes(), contents)
        self.assertEqual(backup.read_bytes(), b"earlier backup")


if __name__ == "__main__":
    unittest.main()
