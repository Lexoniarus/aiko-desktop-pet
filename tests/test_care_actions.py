"""Behavioral parity and boundary tests for modular care actions."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.care_actions import apply_care_action
from aiko_pet.domain import PetState
from aiko_pet.routine import context_at


def stamp(hour: int = 16) -> float:
    return datetime(2026, 10, 12, hour).timestamp()


class CareActionRulesTests(unittest.TestCase):
    def test_pet_state_method_matches_extracted_service(self) -> None:
        moment = stamp()
        for action in ("talk", "feed", "play", "pet", "energy_drink", "sleep"):
            with self.subTest(action=action):
                method_state = PetState(updated_at=moment)
                service_state = PetState(updated_at=moment)
                self.assertEqual(
                    method_state.interact(action, now=moment),
                    apply_care_action(service_state, action, now=moment),
                )
                self.assertEqual(method_state.to_dict(), service_state.to_dict())

    def test_each_care_action_retains_its_specific_effect(self) -> None:
        moment = stamp()
        expected = {
            "talk": ("social", 100.0, "Du möchtest reden"),
            "pet": ("affection", 100.0, "angenehm"),
            "play": ("mood", 98.0, "Heh"),
            "energy_drink": ("energy", 85.0, "geholfen"),
        }
        for action, (attribute, value, reply) in expected.items():
            with self.subTest(action=action):
                state = PetState(updated_at=moment)
                text = apply_care_action(state, action, now=moment)
                self.assertEqual(getattr(state, attribute), value)
                self.assertIn(reply, text)
        state = PetState(updated_at=moment)
        apply_care_action(state, "feed", now=moment)
        self.assertEqual(state.satiety, 100.0)

    def test_meal_credit_is_awarded_only_once_per_window(self) -> None:
        meal_time = stamp(hour=13)
        ctx = context_at(meal_time)
        self.assertIsNotNone(ctx.meal)
        state = PetState(updated_at=meal_time)
        first = apply_care_action(state, "feed", now=meal_time)
        self.assertIn("Danke", first)
        self.assertEqual(state.meals_today, [ctx.meal])
        second = apply_care_action(state, "feed", now=meal_time + 1)
        self.assertIn("Snack", second)
        self.assertEqual(state.meals_today, [ctx.meal])

    def test_rejected_actions_leave_sleep_and_relationship_untouched(self) -> None:
        state = PetState(energy=4, sleeping=True, sleep_origin="manual")
        before = state.to_dict()
        self.assertIn("müde", apply_care_action(state, "play", now=stamp()))
        self.assertEqual(before, state.to_dict())
        with self.assertRaises(ValueError):
            apply_care_action(state, "unknown", now=stamp())
        self.assertEqual(before, state.to_dict())

    def test_full_drink_does_not_wake_aiko(self) -> None:
        state = PetState(energy=100, sleeping=True, sleep_origin="manual")
        self.assertIn("voll", apply_care_action(state, "energy_drink", now=stamp()))
        self.assertTrue(state.sleeping)
        self.assertEqual(state.energy, 100)

    def test_manual_sleep_and_user_care_do_not_lose_night_override(self) -> None:
        night_time = datetime(2026, 10, 12, 23, 45).timestamp()
        context = context_at(night_time)
        self.assertTrue(context.night)
        state = PetState(updated_at=night_time)
        self.assertIn("Zzz", apply_care_action(state, "sleep", now=night_time))
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "manual")
        apply_care_action(state, "talk", now=night_time + 1)
        self.assertFalse(state.sleeping)
        self.assertEqual(state.auto_sleep_night, context.night_key)

    def test_drinks_and_sleep_never_credit_friendship(self) -> None:
        state = PetState(updated_at=stamp())
        before = state.friendship
        apply_care_action(state, "energy_drink", now=stamp())
        apply_care_action(state, "sleep", now=stamp() + 1)
        self.assertEqual(state.friendship, before)


if __name__ == "__main__":
    unittest.main()
