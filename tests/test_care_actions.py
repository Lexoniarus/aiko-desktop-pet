"""Behavioral parity and boundary tests for modular care actions."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.care_actions import plan_care_action
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.ui.view_models.care_text import format_care_response


def stamp(hour: int = 16) -> float:
    return datetime(2026, 10, 12, hour).timestamp()


class CareActionRulesTests(unittest.TestCase):
    def test_pet_state_method_follows_pure_care_plan(self) -> None:
        moment = stamp()
        for action in ("talk", "feed", "play", "pet", "energy_drink", "sleep"):
            with self.subTest(action=action):
                state = PetState(updated_at=moment)
                before = encode_pet_state(state)
                plan = plan_care_action(state, action, now=moment)
                self.assertEqual(encode_pet_state(state), before)
                self.assertEqual(
                    state.interact(action, now=moment), plan.result,
                )

    def test_each_care_action_retains_its_specific_effect(self) -> None:
        moment = stamp()
        expected = {
            "talk": ("social", 100.0, "Du möchtest reden"),
            "pet": ("affection", 100.0, "angenehm"),
            "energy_drink": ("energy", 85.0, "geholfen"),
        }
        for action, (attribute, value, reply) in expected.items():
            with self.subTest(action=action):
                state = PetState(updated_at=moment)
                text = format_care_response(state.interact(action, now=moment))
                self.assertEqual(getattr(state, attribute), value)
                self.assertIn(reply, text)
        state = PetState(updated_at=moment)
        state.interact("feed", now=moment)
        self.assertEqual(state.satiety, 100.0)
        before = encode_pet_state(state)
        self.assertIn("Spiel", format_care_response(state.interact("play", now=moment)))
        self.assertEqual(encode_pet_state(state), before)

    def test_meal_credit_is_awarded_only_once_per_window(self) -> None:
        meal_time = stamp(hour=13)
        ctx = context_at(meal_time)
        self.assertIsNotNone(ctx.meal)
        state = PetState(updated_at=meal_time)
        first = format_care_response(state.interact("feed", now=meal_time))
        self.assertIn("Danke", first)
        self.assertEqual(state.meals_today, [ctx.meal])
        second = format_care_response(state.interact("feed", now=meal_time + 1))
        self.assertIn("satt", second)
        self.assertEqual(state.meals_today, [ctx.meal])

    def test_rejected_actions_leave_sleep_and_relationship_untouched(self) -> None:
        state = PetState(energy=4, sleeping=True, sleep_origin="manual")
        before = encode_pet_state(state)
        self.assertIn("müde", format_care_response(state.interact("play", now=stamp())))
        self.assertEqual(before, encode_pet_state(state))
        with self.assertRaises(ValueError):
            state.interact("unknown", now=stamp())
        self.assertEqual(before, encode_pet_state(state))

    def test_full_drink_does_not_wake_aiko(self) -> None:
        state = PetState(energy=100, sleeping=True, sleep_origin="manual")
        result = state.interact("energy_drink", now=stamp())
        self.assertIn("voll", format_care_response(result))
        self.assertTrue(state.sleeping)
        self.assertEqual(state.energy, 100)

    def test_manual_sleep_and_user_care_do_not_lose_night_override(self) -> None:
        night_time = datetime(2026, 10, 12, 23, 45).timestamp()
        context = context_at(night_time)
        self.assertTrue(context.night)
        state = PetState(updated_at=night_time)
        result = state.interact("sleep", now=night_time)
        self.assertIn("Zzz", format_care_response(result))
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "manual")
        state.interact("talk", now=night_time + 1)
        self.assertFalse(state.sleeping)
        self.assertEqual(state.auto_sleep_night, context.night_key)

    def test_drinks_and_sleep_never_credit_friendship(self) -> None:
        state = PetState(updated_at=stamp())
        before = state.friendship
        state.interact("energy_drink", now=stamp())
        state.interact("sleep", now=stamp() + 1)
        self.assertEqual(state.friendship, before)


if __name__ == "__main__":
    unittest.main()
