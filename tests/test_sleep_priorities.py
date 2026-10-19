"""Sleep priorities through the actual aggregate and chronological time path."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.sleep import SleepContext, SleepEpisode
from aiko_pet.pet.state import PetState


def stamp(hour: int, minute: int = 0, day: int = 12) -> float:
    return datetime(2026, 10, day, hour, minute).timestamp()


QUIET = SleepContext(idle_seconds=1800, observed=True)
ACTIVE = SleepContext(idle_seconds=0, active_seconds=120, observed=True)


class SleepPriorityTests(unittest.TestCase):
    def test_closed_night_starts_at_2315_and_wakes_historically(self):
        pet = PetState(energy=40, updated_at=stamp(23))
        pet.advance(stamp(12, day=13), auto_routine=True)
        self.assertFalse(pet.sleeping)
        self.assertAlmostEqual(pet.energy, 82.375, delta=0.04)
        self.assertEqual(pet.lived_seconds, 13 * 3600)

    def test_full_energy_does_not_end_main_sleep(self):
        pet = PetState(energy=100, updated_at=stamp(23))
        pet.interact("sleep", now=stamp(23))
        pet.advance(stamp(3, day=13), auto_routine=True)
        self.assertTrue(pet.sleeping)
        self.assertEqual(pet.energy, 100)
        pet.advance(stamp(7, day=13), auto_routine=True)
        self.assertFalse(pet.sleeping)

    def test_manual_wake_protection_survives_save_and_exhaustion(self):
        pet = PetState(energy=8, updated_at=stamp(23))
        pet.interact("sleep", now=stamp(23))
        pet.interact("sleep", now=stamp(23))
        pet = decode_pet_state(encode_pet_state(pet))
        pet.advance(stamp(23, 29), auto_routine=True)
        self.assertFalse(pet.sleeping)
        pet.advance(stamp(23, 30), auto_routine=True)
        self.assertTrue(pet.sleeping)
        self.assertEqual(pet.sleep_episode.kind, "recovery")

    def test_manual_sleep_outside_window_is_protected_then_ends(self):
        pet = PetState(energy=80, updated_at=stamp(12))
        pet.interact("sleep", now=stamp(12))
        for minute in range(1, 30):
            pet.advance(stamp(12, minute), auto_routine=True, sleep_context=ACTIVE)
            self.assertTrue(pet.sleeping)
        pet.advance(stamp(12, 30), auto_routine=True, sleep_context=ACTIVE)
        self.assertFalse(pet.sleeping)

    def test_main_return_needs_actual_four_hours_and_energy_60(self):
        pet = PetState(energy=40, updated_at=stamp(23))
        pet.interact("sleep", now=stamp(23))
        pet.advance(stamp(2, 59, day=13), auto_routine=True, sleep_context=ACTIVE)
        self.assertTrue(pet.sleeping)
        pet.advance(stamp(3, day=13), auto_routine=True, sleep_context=ACTIVE)
        self.assertFalse(pet.sleeping)

    def test_early_main_wake_requires_energy_at_least_60(self):
        for energy, sleeping in ((59.99, True), (60, False)):
            with self.subTest(energy=energy):
                pet = PetState(
                    energy=energy, sleeping=True, updated_at=stamp(3, day=13),
                    lived_seconds=4 * 3600,
                    sleep_episode=SleepEpisode(
                        "main", 0, 4 * 3600, stamp(7, day=13),
                    ),
                )
                pet.advance(stamp(3, day=13), auto_routine=True, sleep_context=ACTIVE)
                self.assertEqual(pet.sleeping, sleeping)

    def test_single_jitter_does_not_wake(self):
        pet = PetState(energy=80, updated_at=stamp(23))
        pet.interact("sleep", now=stamp(23))
        pet.advance(
            stamp(6, day=13),
            auto_routine=True,
            sleep_context=SleepContext(idle_seconds=0, observed=True),
        )
        self.assertTrue(pet.sleeping)

    def test_low_energy_at_endpoint_continues_until_40(self):
        pet = PetState(energy=20, updated_at=stamp(6))
        pet.interact("sleep", now=stamp(6))
        pet.advance(stamp(7), auto_routine=True, sleep_context=ACTIVE)
        self.assertTrue(pet.sleeping)
        pet.advance(stamp(9), auto_routine=True, sleep_context=ACTIVE)
        self.assertFalse(pet.sleeping)
        self.assertGreater(pet.energy, 38)

    def test_exhaustion_waits_for_committed_interaction(self):
        pet = PetState(energy=8, updated_at=stamp(12))
        pet.advance(
            stamp(12),
            auto_routine=True,
            sleep_context=SleepContext(blocked=True, observed=True),
        )
        self.assertFalse(pet.sleeping)
        pet.advance(stamp(12), auto_routine=True, sleep_context=ACTIVE)
        self.assertEqual(pet.sleep_episode.kind, "recovery")
        pet.advance(stamp(16, 16), auto_routine=True, sleep_context=ACTIVE)
        self.assertFalse(pet.sleeping)
        self.assertGreaterEqual(pet.energy, 39.9)

    def test_quiet_day_nap_requires_low_energy_and_lasts_75_minutes(self):
        for energy, expected in ((26, False), (25, True)):
            pet = PetState(energy=energy, updated_at=stamp(12))
            pet.advance(stamp(12), auto_routine=True, sleep_context=QUIET)
            self.assertEqual(pet.sleeping, expected)
            if expected:
                pet.advance(stamp(13, 14), auto_routine=True, sleep_context=QUIET)
                self.assertTrue(pet.sleeping)
                pet.advance(stamp(13, 15), auto_routine=True, sleep_context=QUIET)
                self.assertFalse(pet.sleeping)

    def test_manual_nap_at_extreme_exhaustion_becomes_recovery_after_grace(self):
        pet = PetState(energy=1, updated_at=stamp(12))
        pet.interact("sleep", now=stamp(12))
        pet.advance(stamp(12, 30), auto_routine=True, sleep_context=ACTIVE)
        self.assertEqual(pet.sleep_episode.kind, "recovery")
        pet.advance(stamp(15), auto_routine=True, sleep_context=ACTIVE)
        self.assertTrue(pet.sleeping)
        pet.advance(stamp(17, 15), auto_routine=True, sleep_context=ACTIVE)
        self.assertFalse(pet.sleeping)

    def test_unknown_daytime_cannot_prove_a_nap(self):
        pet = PetState(energy=24, updated_at=stamp(12))
        pet.advance(stamp(13), auto_routine=True)
        self.assertFalse(pet.sleeping)

    def test_shifted_expected_window_and_disabled_routine(self):
        shifted = SleepContext(8 * 60, 16 * 60)
        pet = PetState(energy=40, updated_at=stamp(8))
        pet.advance(stamp(15), auto_routine=True, sleep_context=shifted)
        self.assertTrue(pet.sleeping)
        pet.advance(stamp(17), auto_routine=True, sleep_context=shifted)
        self.assertFalse(pet.sleeping)
        off = PetState(energy=8, updated_at=stamp(23))
        off.advance(stamp(7, day=13), auto_routine=False)
        self.assertFalse(off.sleeping)
        self.assertEqual(off.energy, 0)

    def test_care_break_preserves_actual_sleep_without_counting_awake_time(self):
        pet = PetState(energy=40, updated_at=stamp(23))
        pet.interact("sleep", now=stamp(23))
        pet.advance(stamp(1, day=13), auto_routine=True)
        started = pet.sleep_episode.started
        pet.begin_sleep_care(search=True)
        pet.advance(stamp(1, 5, day=13), auto_routine=True)
        pet.end_sleep_care(failed=True)
        pet.advance(stamp(3, day=13), auto_routine=True)
        self.assertEqual(pet.sleep_episode.started, started)
        self.assertAlmostEqual(pet.sleep_episode.slept_seconds, 4 * 3600 - 300)
        self.assertTrue(pet.sleep_episode.food_failed)

    def test_invalid_episode_fields_are_rejected_before_replacing_history(self):
        from aiko_pet.infrastructure.sleep_codec import decode_sleep, encode_sleep

        pet = PetState(updated_at=stamp(23))
        pet.interact("sleep", now=stamp(23))
        original = encode_sleep(pet.sleep_episode)
        for key, value in (
            ("started", 1),
            ("slept_seconds", -1),
            ("protect_until", 1801),
            ("care_break", 1),
            ("intake_until", float("nan")),
            ("failed_food_sources", ["x", "x"]),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                decode_sleep({**original, key: value}, 0)

    def test_latest_manual_command_wins_and_explicit_care_wakes(self):
        pet = PetState(updated_at=stamp(23))
        for _ in range(3):
            pet.interact("sleep", now=stamp(23))
        self.assertTrue(pet.sleeping)
        pet.interact("pet", now=stamp(23))
        self.assertFalse(pet.sleeping)
        pet.advance(stamp(23, 29), auto_routine=True)
        self.assertFalse(pet.sleeping)
        pet.advance(stamp(23, 30), auto_routine=True)
        self.assertTrue(pet.sleeping)
