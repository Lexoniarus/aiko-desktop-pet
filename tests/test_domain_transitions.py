"""Pure domain decisions and PetState-owned mutation regression coverage."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.care_actions import (
    CareTransition,
    plan_care_action,
)
from aiko_pet.pet.friendship import (
    calculate_friendship_reward,
)
from aiko_pet.pet.lifecycle import (
    calculate_daily_routine,
    plan_pet_time,
)
from aiko_pet.pet.need_decay import calculate_need_decay
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState

START = datetime(2026, 10, 12, 12).timestamp()


class DomainTransitionTests(unittest.TestCase):
    def test_care_plans_do_not_mutate_pet_or_saved_history(self) -> None:
        for action in ("pet", "talk", "feed", "play", "sleep", "energy_drink"):
            with self.subTest(action=action):
                state = PetState(
                    updated_at=START, satiety=22, mood=30, energy=65,
                    social=25, affection=35, friendship=60,
                )
                before = encode_pet_state(state)
                transition = plan_care_action(state, action, now=START)
                self.assertIsInstance(transition, CareTransition)
                self.assertEqual(encode_pet_state(state), before)
                with self.assertRaises(FrozenInstanceError):
                    setattr(transition, "changed", False)

    def test_care_plans_match_aggregate_results(self) -> None:
        for action in ("pet", "talk", "feed", "play", "sleep", "energy_drink"):
            with self.subTest(action=action):
                current = PetState(
                    updated_at=START, satiety=20, mood=20,
                    energy=65, social=20, affection=20,
                )
                planned = plan_care_action(current, action, now=START)
                before = encode_pet_state(current)
                self.assertEqual(encode_pet_state(current), before)
                self.assertEqual(current.interact(action, now=START), planned.result)
                self.assertEqual(current.sleeping, planned.sleeping)
                self.assertEqual(current.meals_date, planned.meals_date)

    def test_rejected_care_preserves_every_field_even_during_sleep(self) -> None:
        for action, energy in (("play", 4), ("energy_drink", 100)):
            with self.subTest(action=action):
                state = PetState(
                    energy=energy, sleeping=True, sleep_origin="manual",
                    updated_at=START,
                )
                before = encode_pet_state(state)
                plan = plan_care_action(state, action, now=START)
                self.assertFalse(plan.changed)
                self.assertEqual(state.interact(action, now=START), plan.result)
                self.assertEqual(encode_pet_state(state), before)

    def test_need_and_friendship_evaluations_are_pure(self) -> None:
        state = PetState(
            updated_at=START, friendship=40, affection=25, social=18,
        )
        previous = encode_pet_state(state)
        needs = calculate_need_decay(state, 1.0, context=None, effort=0.9)
        friendship = calculate_friendship_reward(state, "pet", START, 25)
        self.assertEqual(encode_pet_state(state), previous)
        self.assertNotEqual(needs.energy, state.energy)
        self.assertIsNotNone(friendship)
        assert friendship is not None
        self.assertGreater(friendship.friendship, state.friendship)

    def test_need_policy_and_aggregate_use_identical_values(self) -> None:
        for sleeping in (True, False):
            for effort in (None, 0.0, 1.0):
                with self.subTest(sleeping=sleeping, effort=effort):
                    state = PetState(
                        satiety=60, mood=40, energy=50,
                        social=15, affection=18, sleeping=sleeping,
                        sleep_origin="manual" if sleeping else "",
                        updated_at=START,
                    )
                    before = encode_pet_state(state)
                    expected = calculate_need_decay(state, 0.5, None, effort)
                    self.assertEqual(encode_pet_state(state), before)
                    state._decay(0.5, None, effort)
                    for key in ("satiety", "mood", "energy", "social", "affection"):
                        with self.subTest(need=key):
                            self.assertAlmostEqual(
                                getattr(state, key), getattr(expected, key),
                            )

    def test_friendship_transition_matches_aggregate_history(self) -> None:
        state = PetState(
            friendship=20, affection=30, updated_at=START,
        )
        original = encode_pet_state(state)
        decision = calculate_friendship_reward(state, "pet", START, 30)
        self.assertIsNotNone(decision)
        assert decision is not None
        self.assertEqual(encode_pet_state(state), original)
        state._credit_friendship("pet", START, 30)
        self.assertEqual(state.friendship, decision.friendship)
        self.assertEqual(state.friendship_day, decision.day)
        self.assertEqual(state.friendship_gained_today, decision.gained_today)
        self.assertEqual(tuple(state.care_types_today), decision.care_types)
        unchanged = encode_pet_state(state)
        state._credit_friendship("pet", START + 10, 0)
        self.assertEqual(encode_pet_state(state), unchanged)

    def test_timeline_plan_never_modifies_state(self) -> None:
        state = PetState(updated_at=START, energy=20)
        before = encode_pet_state(state)
        clock = context_at(START + 3600)
        transition = calculate_daily_routine(state, clock, allow_nap=True)
        steps = plan_pet_time(
            state.updated_at, START + 3600,
            auto_routine=True, effort=0.8,
        )
        self.assertIsNotNone(steps)
        self.assertGreater(len(steps or ()), 0)
        self.assertEqual(encode_pet_state(state), before)
        self.assertTrue(transition.sleeping)
        self.assertFalse(state.sleeping)

    def test_routine_policy_matches_aggregate_transition(self) -> None:
        for auto in (True, False):
            with self.subTest(auto_routine=auto):
                state = PetState(updated_at=START, energy=45)
                steps = plan_pet_time(
                    state.updated_at, START + 3600,
                    auto_routine=auto, effort=0.85,
                )
                self.assertIsNotNone(steps)
                state.advance(START + 3600, auto_routine=auto, effort=0.85)
                self.assertEqual(state.updated_at, START + 3600)
        context = context_at(START + 12 * 3600)
        state = PetState(updated_at=START)
        planned = calculate_daily_routine(state, context, allow_bedtime=True)
        state.update_daily_routine(context, allow_bedtime=True)
        self.assertEqual(state.sleeping, planned.sleeping)
        self.assertEqual(state.sleep_origin, planned.sleep_origin)

    def test_invalid_time_never_mutates_pet(self) -> None:
        state = PetState(updated_at=START)
        before = encode_pet_state(state)
        self.assertIsNone(plan_pet_time(START, float("nan")))
        state.advance(float("nan"))
        self.assertEqual(encode_pet_state(state), before)


if __name__ == "__main__":
    unittest.main()
