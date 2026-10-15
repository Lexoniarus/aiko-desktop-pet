"""Food balance and save compatibility without Tk or operating system APIs."""

from __future__ import annotations

from aiko_pet.ui.view_models.care_text import format_care_response

from aiko_pet.infrastructure.pet_codec import (
    decode_food_state, decode_pet_state, encode_pet_state,
)

import unittest
from datetime import datetime

from aiko_pet.pet.food import (
    FOOD_BALANCE, FOOD_CATALOG, FoodActivity, FoodId, FoodState,
    advance_food, eat_food, hunger_activity_multiplier, is_repeated_food,
)
from aiko_pet.pet.state import PetState


def clock(hour: int = 8) -> float:
    return datetime(2026, 10, 13, hour).timestamp()


class FoodPolicyTests(unittest.TestCase):
    def test_all_ten_foods_have_distinct_immediate_and_delayed_effects(self) -> None:
        self.assertEqual(
            set(FOOD_CATALOG),
            {"onigiri", "sandwich", "taiyaki", "apple", "dango",
             "donut", "cookie", "melonpan", "cupcake", "dorayaki"},
        )
        immediate = {
            profile.instant_satiety_points for profile in FOOD_CATALOG.values()
        }
        reserves = {
            profile.digest_reserve_minutes for profile in FOOD_CATALOG.values()
        }
        self.assertEqual(len(immediate), 10)
        self.assertEqual(len(reserves), 10)
        self.assertGreater(
            FOOD_CATALOG["sandwich"].instant_satiety_points,
            FOOD_CATALOG["dango"].instant_satiety_points,
        )

    def test_sandwich_holds_satiety_longer_than_dango(self) -> None:
        sandwich = eat_food(FoodState(), 35, "sandwich")
        dango = eat_food(FoodState(), 35, "dango")
        self.assertTrue(sandwich.accepted)
        self.assertGreater(sandwich.food.remaining_digest_minutes, 100)
        x = advance_food(sandwich.food, 65, 1.5, sleeping=False)
        y = advance_food(dango.food, 65, 1.5, sleeping=False)
        self.assertGreater(x.satiety, y.satiety)
        self.assertLess(x.food.remaining_digest_minutes, 100)

    def test_hunger_accelerates_when_no_food_is_eaten(self) -> None:
        normal = advance_food(FoodState(), 100, 2, sleeping=False)
        hungry = advance_food(
            FoodState(awake_hours_since_last_food=6), 100, 2,
            sleeping=False,
        )
        self.assertLess(hungry.satiety, normal.satiety)
        self.assertGreaterEqual(hungry.satiety, 0.0)

    def test_both_real_activity_axes_increase_hunger_but_are_bounded(self) -> None:
        calm = advance_food(FoodState(), 100, 2, sleeping=False)
        cpu = advance_food(
            FoodState(), 100, 2, sleeping=False,
            activity=FoodActivity(hardware_load=1),
        )
        typing = advance_food(
            FoodState(), 100, 2, sleeping=False,
            activity=FoodActivity(user_input_activity=1),
        )
        both = advance_food(
            FoodState(), 100, 2, sleeping=False,
            activity=FoodActivity(1, 1),
        )
        self.assertLess(cpu.satiety, calm.satiety)
        self.assertLess(typing.satiety, calm.satiety)
        self.assertLess(both.satiety, min(cpu.satiety, typing.satiety))
        self.assertLessEqual(
            hunger_activity_multiplier(FoodActivity(1, 1)),
            1 + FOOD_BALANCE.maximum_combined_activity_bonus,
        )

    def test_repetition_changes_mood_but_never_nutrition(self) -> None:
        food = FoodState()
        outcomes = []
        for _ in range(3):
            outcome = eat_food(food, 30, "onigiri")
            outcomes.append(outcome)
            food = outcome.food
        self.assertFalse(outcomes[0].repetitive)
        self.assertFalse(outcomes[1].repetitive)
        self.assertTrue(outcomes[2].repetitive)
        self.assertEqual(outcomes[0].satiety, outcomes[2].satiety)
        self.assertLess(outcomes[2].mood_change, outcomes[0].mood_change)
        self.assertFalse(is_repeated_food(
            food, "sandwich",
        ))

    def test_snack_does_not_reset_hours_since_main_meal(self) -> None:
        old = FoodState(
            awake_hours_since_last_food=2,
            awake_hours_since_main_meal=5,
        )
        snack = eat_food(old, 30, "apple")
        self.assertEqual(snack.food.awake_hours_since_main_meal, 5)
        self.assertEqual(snack.food.awake_hours_since_last_food, 0)
        meal = eat_food(old, 30, "sandwich")
        self.assertEqual(meal.food.awake_hours_since_main_meal, 0)

    def test_sleep_is_gentle_and_never_invents_user_activity(self) -> None:
        slept = advance_food(
            FoodState(), 75, 8, sleeping=True,
            activity=FoodActivity(1, 1),
        )
        self.assertAlmostEqual(slept.satiety, 75 - 8 * 1.4, places=3)
        self.assertEqual(slept.food.awake_hours_since_last_food, 0)

    def test_rejected_overfeeding_leaves_entire_state_untouched(self) -> None:
        pet = PetState(satiety=99)
        before = encode_pet_state(pet)
        reply = format_care_response(pet.interact("feed", now=clock(), food_id="sandwich"))
        self.assertIn("satt", reply)
        self.assertEqual(encode_pet_state(pet), before)

    def test_corrupt_food_save_is_bounded_and_old_save_is_supported(self) -> None:
        old = decode_pet_state({"satiety": 41}, now=clock())
        self.assertEqual(old.food, FoodState())
        broken = decode_food_state({
            "remaining_digest_minutes": 1000000,
            "awake_hours_since_last_food": float("nan"),
            "awake_hours_since_main_meal": -20,
            "recent_food_ids": ["bad", "apple", 55, "dango"],
        })
        self.assertLessEqual(
            broken.remaining_digest_minutes,
            FOOD_BALANCE.maximum_digest_reserve_minutes,
        )
        self.assertEqual(broken.awake_hours_since_last_food, 0)
        self.assertEqual(broken.awake_hours_since_main_meal, 0)
        self.assertEqual(broken.recent_food_ids, ("apple", "dango"))

    def test_food_state_roundtrips_without_offline_digesting(self) -> None:
        pet = PetState(satiety=12, updated_at=clock())
        pet.interact("feed", now=clock(), food_id="sandwich")
        encoded = encode_pet_state(pet)
        reopened = decode_pet_state(encoded, now=clock() + 72 * 3600)
        self.assertEqual(reopened.satiety, pet.satiety)
        self.assertEqual(reopened.food, pet.food)
        self.assertNotIn("user_input_activity", encoded)

    def test_default_feed_uses_known_onigiri_and_invalid_food_is_rejected(
        self,
    ) -> None:
        pet = PetState(satiety=20)
        pet.interact("feed", now=clock())
        self.assertEqual(pet.satiety, 50)
        self.assertEqual(pet.food.last_food_id, "onigiri")
        before = encode_pet_state(pet)
        with self.assertRaises(ValueError):
            pet.interact("talk", now=clock(), food_id="apple")
        self.assertEqual(encode_pet_state(pet), before)

    def test_three_main_meals_and_two_snacks_cover_a_normal_day(self) -> None:
        day = clock()
        pet = PetState(satiety=65, updated_at=day)
        lowest = 100.0
        consumed: dict[int, FoodId] = {
            0: "onigiri", 3: "apple", 6: "sandwich",
            9: "taiyaki", 12: "onigiri",
        }
        for hour in range(16):
            if hour in consumed:
                pet.interact("feed", now=day + hour * 3600,
                             food_id=consumed[hour])
            pet.advance(day + (hour + 1) * 3600, auto_routine=False)
            lowest = min(lowest, pet.satiety)
        self.assertGreaterEqual(lowest, 25)
        self.assertLessEqual(pet.satiety, 100)
        pet.interact("sleep", now=day + 16 * 3600)
        pet.advance(day + 24 * 3600, auto_routine=False)
        self.assertTrue(pet.sleeping)
        self.assertGreater(pet.satiety, 0)


if __name__ == "__main__":
    unittest.main()
