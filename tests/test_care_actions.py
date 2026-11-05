"""Behavioral parity and boundary tests for modular care actions."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.care_actions import plan_care_action
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.presentation.view_models.care_text import format_care_response


def stamp(hour: int = 16) -> float:
    return datetime(2026, 10, 12, hour).timestamp()


def timestamp(day: str = "2026-10-12", hour: int = 12) -> float:
    return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone().timestamp()


class CareActionRulesTests(unittest.TestCase):
    def test_pet_state_method_follows_pure_care_plan(self) -> None:
        moment = stamp()
        for action in ("talk", "feed", "play", "pet", "energy_drink", "sleep"):
            with self.subTest(action=action):
                state = PetState(
                    updated_at=moment, satiety=20, mood=20, energy=65,
                    social=20, affection=20,
                )
                before = encode_pet_state(state)
                plan = plan_care_action(state, action, now=moment)
                self.assertEqual(encode_pet_state(state), before)
                self.assertEqual(
                    state.interact(action, now=moment),
                    plan.result,
                )
                self.assertEqual(state.sleeping, plan.sleeping)
                self.assertEqual(state.meals_date, plan.meals_date)

    def test_each_care_action_retains_its_specific_effect(self) -> None:
        moment = stamp()
        expected = {
            "talk": ("social", 100.0, "reden"),
            "pet": ("affection", 100.0, "streicheln"),
            "energy_drink": ("energy", 85.0, "Schwung"),
        }
        for action, (attribute, value, reply) in expected.items():
            with self.subTest(action=action):
                state = PetState(updated_at=moment, friendship=50)
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
        result = state.interact("play", now=stamp())
        self.assertIn("Schlaf", format_care_response(result))
        self.assertEqual(before, encode_pet_state(state))
        with self.assertRaises(ValueError):
            state.interact("unknown", now=stamp())
        self.assertEqual(before, encode_pet_state(state))

    def test_full_drink_does_not_wake_aiko(self) -> None:
        state = PetState(energy=100, sleeping=True, sleep_origin="manual")
        result = state.interact("energy_drink", now=stamp())
        self.assertIn("wach genug", format_care_response(result))
        self.assertTrue(state.sleeping)
        self.assertEqual(state.energy, 100)

    def test_manual_sleep_and_user_care_do_not_lose_night_override(self) -> None:
        night_time = datetime(2026, 10, 12, 23, 45).timestamp()
        context = context_at(night_time)
        self.assertTrue(context.night)
        state = PetState(updated_at=night_time)
        result = state.interact("sleep", now=night_time)
        self.assertIn("Schlafen", format_care_response(result))
        self.assertTrue(state.sleeping)
        self.assertEqual(state.sleep_origin, "manual")
        state.interact("talk", now=night_time + 1)
        self.assertFalse(state.sleeping)
        self.assertEqual(state.auto_sleep_night, context.night_key)

    def test_drink_and_sleep_do_not_give_instant_friendship(self) -> None:
        state = PetState(updated_at=stamp())
        before = state.friendship
        state.interact("energy_drink", now=stamp())
        self.assertAlmostEqual(state.friendship - before, 0)
        before = state.friendship
        state.interact("sleep", now=stamp() + 1)
        self.assertEqual(state.friendship, before)

    def test_talk_is_distinct_from_play_and_food(self):
        state = PetState(social=12, satiety=28, mood=30, energy=60, affection=21)
        state.interact("talk", now=timestamp())
        self.assertEqual(state.social, 38)
        self.assertEqual(state.affection, 21)
        self.assertEqual(state.mood, 30)
        self.assertEqual(state.satiety, 28)
        self.assertEqual(state.energy, 59)
        self.assertEqual(state.friendship, 15)

    def test_feeding_does_not_substitute_for_social_care(self):
        state = PetState(social=8, satiety=10, affection=50)
        state.interact("feed", now=timestamp())
        self.assertEqual(state.social, 9)
        self.assertEqual(state.satiety, 40)
        state.interact("pet", now=timestamp() + 1)
        self.assertEqual(state.social, 11)
        self.assertEqual(state.affection, 75)
        before = encode_pet_state(state)
        state.interact("play", now=timestamp() + 2)
        self.assertEqual(encode_pet_state(state), before)

    def test_energy_drink_is_exactly_ten_points_and_can_be_stacked(self):
        state = PetState(energy=47, sleeping=True)
        start = timestamp()
        for n in range(5):
            state.interact("energy_drink", now=start + n)
        self.assertEqual(state.energy, 97)
        self.assertFalse(state.sleeping)
        state.interact("energy_drink", now=start + 7)
        self.assertEqual(state.energy, 100)
        before = encode_pet_state(state)
        self.assertIn(
            "wach genug",
            format_care_response(state.interact("energy_drink", now=start + 8)),
        )
        self.assertEqual(before, encode_pet_state(state))
        self.assertEqual(state.friendship, 15)

    def test_energy_drink_never_increases_hunger_or_social(self):
        state = PetState(energy=0, satiety=41, mood=55, social=27)
        state.interact("energy_drink", now=timestamp())
        self.assertEqual((state.energy, state.satiety, state.social), (10, 41, 27))

    def test_sleep_toggle_and_feeding_wakes(self):
        state = PetState()
        state.interact("sleep")
        self.assertTrue(state.sleeping)
        state.interact("feed")
        self.assertFalse(state.sleeping)
        self.assertEqual(state.satiety, 100)

    def test_night_energy_drink_prevents_immediate_auto_sleep(self):
        stamp = timestamp(hour=23) + 45 * 60
        state = PetState(
            updated_at=stamp, energy=18, sleeping=True, sleep_origin="manual"
        )
        state.interact("energy_drink", now=stamp)
        self.assertFalse(state.sleeping)
        state.advance(stamp + 1, auto_routine=True, allow_bedtime=True)
        self.assertFalse(state.sleeping)
        self.assertAlmostEqual(state.energy, 28, places=2)

    def test_manual_night_wake_also_honors_user_intervention(self):
        stamp = timestamp(hour=23) + 45 * 60
        state = PetState(updated_at=stamp, sleeping=True, sleep_origin="manual")
        state.interact("sleep", now=stamp)
        state.advance(stamp + 1, auto_routine=True)
        self.assertFalse(state.sleeping)

    def test_pet_primarily_refills_affection_and_never_gives_energy(self):
        state = PetState(affection=30, mood=25, social=40, energy=50)
        state.interact("pet", now=timestamp())
        self.assertEqual(state.affection, 55)
        self.assertEqual(state.mood, 25)
        self.assertEqual(state.social, 42)
        self.assertEqual(state.energy, 50)


if __name__ == "__main__":
    unittest.main()
