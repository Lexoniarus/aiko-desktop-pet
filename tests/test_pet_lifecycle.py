"""Regression coverage for headless need decay and daily catch-up."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from datetime import datetime

from aiko_pet.pet.lifecycle import MAX_CATCHUP_SECONDS, MAX_LIVE_EFFORT_SECONDS
from aiko_pet.pet.state import PetState
from aiko_pet.pet.need_decay import apply_need_decay
from aiko_pet.pet.lifecycle import (
    MAX_CATCHUP_SECONDS as POLICY_CATCHUP,
    MAX_LIVE_EFFORT_SECONDS as POLICY_LIVE_WINDOW,
    advance_pet_time,
    apply_daily_routine,
)
from aiko_pet.pet.routine import context_at


@dataclass
class Needs:
    sleeping: bool = False
    satiety: float = 75.0
    mood: float = 75.0
    energy: float = 75.0
    social: float = 75.0
    affection: float = 75.0


def local_stamp(hour: int = 12, minute: int = 0) -> float:
    return datetime(2026, 10, 12, hour, minute).timestamp()


class NeedDecayTests(unittest.TestCase):
    def test_normal_waking_decay_does_not_require_pet_state(self) -> None:
        needs = Needs()
        apply_need_decay(needs, 1, context=None)
        self.assertEqual(needs.satiety, 72.0)
        self.assertEqual(needs.mood, 73.0)
        self.assertAlmostEqual(needs.energy, 72.8)
        self.assertEqual(needs.social, 73.2)
        self.assertEqual(needs.affection, 73.65)

    def test_sleep_replenishes_energy_without_friendship_change(self) -> None:
        needs = Needs(sleeping=True, energy=40)
        apply_need_decay(needs, 1, context=None, effort=1.0)
        self.assertEqual(needs.energy, 62)
        self.assertEqual(needs.satiety, 73.6)
        self.assertEqual(needs.affection, 74.75)

    def test_heavy_work_increases_waking_drain(self) -> None:
        relaxed = Needs()
        working = Needs()
        apply_need_decay(relaxed, 1, context=None, effort=0)
        apply_need_decay(working, 1, context=None, effort=1)
        self.assertLess(working.satiety, relaxed.satiety)
        self.assertLess(working.energy, relaxed.energy)
        self.assertLess(working.mood, relaxed.mood)
        self.assertEqual(working.affection, relaxed.affection)


class PetTimelineTests(unittest.TestCase):
    def test_save_keys_still_match_original_schema(self) -> None:
        expected = {
            "satiety", "mood", "energy", "social", "affection", "friendship",
            "friendship_day", "friendship_gained_today", "care_types_today",
            "care_last_rewards", "sleeping", "updated_at", "meals_date",
            "meals_today", "sleep_origin", "auto_sleep_night", "nap_until",
            "auto_nap_day",
        }
        self.assertEqual(set(PetState().to_dict()), expected)

    def test_legacy_constants_are_preserved(self) -> None:
        self.assertEqual(MAX_CATCHUP_SECONDS, POLICY_CATCHUP)
        self.assertEqual(MAX_LIVE_EFFORT_SECONDS, POLICY_LIVE_WINDOW)

    def test_public_advance_and_service_produce_identical_serialization(self) -> None:
        moment = local_stamp(hour=15)
        for routine in (True, False):
            with self.subTest(routine=routine):
                old = PetState(updated_at=moment)
                new = PetState(updated_at=moment)
                old.advance(moment + 3600, auto_routine=routine, effort=0.8)
                advance_pet_time(
                    new, moment + 3600, auto_routine=routine, effort=0.8,
                )
                self.assertEqual(old.to_dict(), new.to_dict())

    def test_catchup_is_bounded_without_routine(self) -> None:
        state = PetState(updated_at=local_stamp())
        advance_pet_time(state, local_stamp() + 86400.0 * 7)
        self.assertEqual(state.satiety, 51.0)
        self.assertEqual(state.mood, 59.0)
        self.assertAlmostEqual(state.energy, 57.4)

    def test_telemetry_is_not_extrapolated_across_offline_hours(self) -> None:
        calm = PetState(updated_at=local_stamp())
        working = PetState(updated_at=local_stamp())
        advance_pet_time(calm, local_stamp() + 3600.0, effort=None)
        advance_pet_time(working, local_stamp() + 3600.0, effort=1.0)
        self.assertGreater(calm.satiety - working.satiety, 0)
        self.assertLess(calm.satiety - working.satiety, 0.1)

    def test_boolean_effort_is_not_accepted_as_telemetry(self) -> None:
        first = PetState(updated_at=local_stamp())
        second = PetState(updated_at=local_stamp())
        advance_pet_time(first, local_stamp() + 3600.0, effort=True)
        advance_pet_time(second, local_stamp() + 3600.0, effort=None)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_automatic_sleep_can_be_prevented_by_work(self) -> None:
        context = context_at(local_stamp(hour=23, minute=45))
        state = PetState(updated_at=context.local.timestamp())
        apply_daily_routine(state, context, allow_bedtime=False)
        self.assertFalse(state.sleeping)
        apply_daily_routine(state, context, allow_bedtime=True)
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "routine")
        apply_daily_routine(state, context, allow_bedtime=False)
        self.assertFalse(state.sleeping)


if __name__ == "__main__":
    unittest.main()
