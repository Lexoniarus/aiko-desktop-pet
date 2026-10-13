"""Pure domain decisions and PetState-owned mutation regression coverage."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

from aiko_pet.care_actions import (
    CareTransition,
    apply_care_action,
    plan_care_action,
)
from aiko_pet.domain import PetState
from aiko_pet.friendship import (
    award_friendship_for_care,
    calculate_friendship_reward,
)
from aiko_pet.need_decay import apply_need_decay, calculate_need_decay
from aiko_pet.pet_lifecycle import (
    advance_pet_time,
    apply_daily_routine,
    calculate_daily_routine,
    plan_pet_time,
)
from aiko_pet.routine import context_at

START = datetime(2026, 10, 12, 12).timestamp()


class DomainTransitionTests(unittest.TestCase):
    def test_care_plans_do_not_mutate_pet_or_saved_history(self) -> None:
        for action in ("pet", "talk", "feed", "play", "sleep", "energy_drink"):
            with self.subTest(action=action):
                state = PetState(
                    updated_at=START, satiety=22, mood=30, energy=65,
                    social=25, affection=35, friendship=60,
                )
                before = state.to_dict()
                transition = plan_care_action(state, action, now=START)
                self.assertIsInstance(transition, CareTransition)
                self.assertEqual(state.to_dict(), before)
                with self.assertRaises(FrozenInstanceError):
                    setattr(transition, "changed", False)

    def test_care_plans_match_aggregate_and_legacy_api(self) -> None:
        for action in ("pet", "talk", "feed", "play", "sleep", "energy_drink"):
            with self.subTest(action=action):
                current = PetState(
                    updated_at=START, satiety=20, mood=20,
                    energy=65, social=20, affection=20,
                )
                legacy = PetState.from_dict(current.to_dict(), now=START)
                planned = plan_care_action(current, action, now=START)
                self.assertEqual(current.interact(action, now=START), planned.response)
                self.assertEqual(
                    apply_care_action(legacy, action, now=START),
                    planned.response,
                )
                self.assertEqual(current.to_dict(), legacy.to_dict())

    def test_rejected_care_preserves_every_field_even_during_sleep(self) -> None:
        for action, energy in (("play", 4), ("energy_drink", 100)):
            with self.subTest(action=action):
                state = PetState(
                    energy=energy, sleeping=True, sleep_origin="manual",
                    updated_at=START,
                )
                before = state.to_dict()
                plan = plan_care_action(state, action, now=START)
                self.assertFalse(plan.changed)
                self.assertEqual(state.interact(action, now=START), plan.response)
                self.assertEqual(state.to_dict(), before)

    def test_need_and_friendship_evaluations_are_pure(self) -> None:
        state = PetState(
            updated_at=START, friendship=40, affection=25, social=18,
        )
        previous = state.to_dict()
        needs = calculate_need_decay(state, 1.0, context=None, effort=0.9)
        friendship = calculate_friendship_reward(state, "pet", START, 25)
        self.assertEqual(state.to_dict(), previous)
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
                    reference = PetState.from_dict(state.to_dict(), now=START)
                    apply_need_decay(reference, 0.5, None, effort)
                    state._decay(0.5, None, effort)
                    self.assertEqual(state.to_dict(), reference.to_dict())

    def test_friendship_reward_adapters_preserve_daily_history(self) -> None:
        state = PetState(
            friendship=20, affection=30, updated_at=START,
        )
        reference = PetState.from_dict(state.to_dict(), now=START)
        original = state.to_dict()
        decision = calculate_friendship_reward(state, "pet", START, 30)
        self.assertIsNotNone(decision)
        self.assertEqual(state.to_dict(), original)
        state._credit_friendship("pet", START, 30)
        award_friendship_for_care(reference, "pet", START, 30)
        self.assertEqual(state.to_dict(), reference.to_dict())
        state._credit_friendship("pet", START + 10, 0)
        self.assertEqual(state.friendship, reference.friendship)

    def test_timeline_plan_never_modifies_state(self) -> None:
        state = PetState(updated_at=START, energy=20)
        before = state.to_dict()
        clock = context_at(START + 3600)
        transition = calculate_daily_routine(state, clock, allow_nap=True)
        steps = plan_pet_time(
            state.updated_at, START + 3600,
            auto_routine=True, effort=0.8,
        )
        self.assertIsNotNone(steps)
        self.assertGreater(len(steps or ()), 0)
        self.assertEqual(state.to_dict(), before)
        self.assertTrue(transition.sleeping)
        self.assertFalse(state.sleeping)

    def test_legacy_routine_api_routes_through_pet_methods(self) -> None:
        for auto in (True, False):
            with self.subTest(auto_routine=auto):
                current = PetState(updated_at=START, energy=45)
                reference = PetState(updated_at=START, energy=45)
                current.advance(START + 3600, auto_routine=auto, effort=0.85)
                advance_pet_time(
                    reference, START + 3600, auto_routine=auto, effort=0.85,
                )
                self.assertEqual(current.to_dict(), reference.to_dict())
        context = context_at(START + 12 * 3600)
        current = PetState(updated_at=START)
        reference = PetState(updated_at=START)
        current.update_daily_routine(context, allow_bedtime=True)
        apply_daily_routine(reference, context, allow_bedtime=True)
        self.assertEqual(current.to_dict(), reference.to_dict())

    def test_invalid_time_never_mutates_pet(self) -> None:
        state = PetState(updated_at=START)
        before = state.to_dict()
        self.assertIsNone(plan_pet_time(START, float("nan")))
        state.advance(float("nan"))
        self.assertEqual(state.to_dict(), before)


if __name__ == "__main__":
    unittest.main()
