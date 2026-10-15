"""Regression coverage for headless need decay and daily catch-up."""

from __future__ import annotations

from aiko_pet.infrastructure.pet_codec import encode_pet_state

import unittest
from dataclasses import dataclass
from datetime import datetime

from aiko_pet.pet.lifecycle import MAX_CATCHUP_SECONDS, MAX_LIVE_EFFORT_SECONDS
from aiko_pet.pet.state import PetState
from aiko_pet.pet.need_decay import calculate_need_decay
from aiko_pet.pet.lifecycle import (
    MAX_CATCHUP_SECONDS as POLICY_CATCHUP,
    MAX_LIVE_EFFORT_SECONDS as POLICY_LIVE_WINDOW,
    plan_pet_time,
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
        result = calculate_need_decay(needs, 1, context=None)
        self.assertAlmostEqual(result.satiety, 67.0)
        self.assertGreater(result.mood, 69.0)
        self.assertLess(result.mood, 75.0)
        self.assertAlmostEqual(result.energy, 69.0)
        self.assertEqual(result.social, 67.0)
        self.assertEqual(result.affection, 69.0)
        self.assertEqual(needs.satiety, 75.0)

    def test_sleep_replenishes_energy_without_friendship_change(self) -> None:
        needs = Needs(sleeping=True, energy=40)
        result = calculate_need_decay(needs, 1, context=None, effort=1.0)
        self.assertEqual(result.energy, 62)
        self.assertAlmostEqual(result.satiety, 73.6)
        self.assertEqual(result.affection, 74.75)
        self.assertEqual(needs.energy, 40)

    def test_heavy_work_increases_waking_drain(self) -> None:
        relaxed = Needs()
        working = Needs()
        relaxed_next = calculate_need_decay(relaxed, 1, context=None, effort=0)
        working_next = calculate_need_decay(working, 1, context=None, effort=1)
        self.assertLess(working_next.satiety, relaxed_next.satiety)
        self.assertLess(working_next.energy, relaxed_next.energy)
        self.assertLess(working_next.mood, relaxed_next.mood)
        self.assertEqual(working_next.affection, relaxed_next.affection)
        self.assertEqual(working.energy, relaxed.energy)


class PetTimelineTests(unittest.TestCase):
    def test_save_keys_still_match_original_schema(self) -> None:
        expected = {
            "satiety", "mood", "energy", "social", "affection", "friendship",
            "friendship_day", "friendship_gained_today", "care_types_today",
            "care_last_rewards", "sleeping", "updated_at", "meals_date",
            "meals_today", "sleep_origin", "auto_sleep_night", "nap_until",
            "auto_nap_day", "food", "fun",
        }
        self.assertEqual(set(encode_pet_state(PetState())), expected)

    def test_legacy_constants_are_preserved(self) -> None:
        self.assertEqual(MAX_CATCHUP_SECONDS, POLICY_CATCHUP)
        self.assertEqual(MAX_LIVE_EFFORT_SECONDS, POLICY_LIVE_WINDOW)

    def test_public_advance_consumes_a_bounded_timeline(self) -> None:
        moment = local_stamp(hour=15)
        for routine in (True, False):
            with self.subTest(routine=routine):
                steps = plan_pet_time(
                    moment, moment + 3600,
                    auto_routine=routine, effort=0.8,
                )
                self.assertIsNotNone(steps)
                assert steps is not None
                self.assertAlmostEqual(
                    sum(step.hours for step in steps), 1.0,
                )
                state = PetState(updated_at=moment)
                state.advance(moment + 3600, auto_routine=routine, effort=0.8)
                self.assertEqual(state.updated_at, moment + 3600)

    def test_catchup_is_bounded_without_routine(self) -> None:
        state = PetState(updated_at=local_stamp())
        state.advance( local_stamp() + 86400.0 * 7)
        self.assertLessEqual(state.satiety, 12.0)
        self.assertGreater(state.mood, 0.0)
        self.assertLess(state.mood, 43.0)
        self.assertAlmostEqual(state.energy, 27.0)

    def test_telemetry_is_not_extrapolated_across_offline_hours(self) -> None:
        calm = PetState(updated_at=local_stamp())
        working = PetState(updated_at=local_stamp())
        calm.advance( local_stamp() + 3600.0, effort=None)
        working.advance( local_stamp() + 3600.0, effort=1.0)
        self.assertGreater(calm.satiety - working.satiety, 0)
        self.assertLess(calm.satiety - working.satiety, 0.1)

    def test_boolean_effort_is_not_accepted_as_telemetry(self) -> None:
        first = PetState(updated_at=local_stamp())
        second = PetState(updated_at=local_stamp())
        first.advance( local_stamp() + 3600.0, effort=True)
        second.advance( local_stamp() + 3600.0, effort=None)
        self.assertEqual(encode_pet_state(first), encode_pet_state(second))

    def test_automatic_sleep_can_be_prevented_by_work(self) -> None:
        context = context_at(local_stamp(hour=23, minute=45))
        state = PetState(updated_at=context.local.timestamp())
        state.update_daily_routine( context, allow_bedtime=False)
        self.assertFalse(state.sleeping)
        state.update_daily_routine( context, allow_bedtime=True)
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "routine")
        state.update_daily_routine( context, allow_bedtime=False)
        self.assertFalse(state.sleeping)


if __name__ == "__main__":
    unittest.main()
