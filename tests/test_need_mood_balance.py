"""Approved care/mood examples exercised through actual domain transitions."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.pet.food import FoodActivity, FoodState, advance_food
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.mood import NeedMoodFactors, advance_mood, calculate_need_mood_target
from aiko_pet.pet.state import PetState

NOW = datetime(2026, 10, 19, 7).timestamp()
NEEDS = ("satiety", "energy", "fun", "social", "affection")


class NeedMoodBalanceTests(unittest.TestCase):
    def test_documented_targets_and_combined_shortages(self) -> None:
        self.assertEqual(
            calculate_need_mood_target(NeedMoodFactors(100, 100, 100, 100, 100)), 80,
        )
        self.assertEqual(
            calculate_need_mood_target(NeedMoodFactors(80, 80, 80, 80, 80)), 64,
        )
        for key in NEEDS:
            for value, expected in ((25, 60), (10, 45), (0, 30), (5, 37.5),
                                    (17.5, 52.5)):
                values = dict.fromkeys(NEEDS, 100.0)
                values[key] = value
                with self.subTest(need=key, value=value):
                    self.assertAlmostEqual(calculate_need_mood_target(NeedMoodFactors(**values)),
                                           expected)
        self.assertEqual(
            calculate_need_mood_target(NeedMoodFactors(0, 0, 100, 100, 100)), 8,
        )
        self.assertEqual(
            calculate_need_mood_target(NeedMoodFactors(0, 50, 50, 50, 50)), 12,
        )
        self.assertEqual(calculate_need_mood_target(NeedMoodFactors(0, 0, 0, 0, 0)), 0)

    def test_constant_target_decline_and_recovery_have_real_minute_rates(self) -> None:
        for need, rate in ((40, 1), (25, 3), (10, 6), (0, 10), (17.5, 4.5)):
            with self.subTest(need=need):
                self.assertAlmostEqual(
                    advance_mood(80, 0, 1 / 60, lowest_need=need), 80 - rate,
                )
        for minutes, expected in ((1, 70), (3, 50), (5, 30), (30, 30)):
            self.assertEqual(
                advance_mood(80, 30, minutes / 60, lowest_need=0), expected,
            )
        for minutes, expected in ((0, 30), (10, 50), (15, 60), (25, 80), (40, 80)):
            self.assertEqual(
                advance_mood(30, 80, minutes / 60, lowest_need=100), expected,
            )

    def test_shortages_change_target_without_instant_care_or_game_mood_bonuses(self):
        pet = PetState(satiety=5, social=5, affection=5, energy=50, fun=50,
                       mood=8, updated_at=NOW)
        for action in ("feed", "talk", "pet", "energy_drink", "feed", "feed"):
            pet.interact(action, now=NOW)
            self.assertEqual(pet.mood, 8)
        pet.record_game_experience(GameExperience("rock_paper_scissors", 3), now=NOW)
        self.assertEqual(pet.mood, 8)
        pet.advance(NOW + 60)
        self.assertEqual(pet.mood, 10)

    def test_relationship_does_not_add_a_generic_mood_bonus(self) -> None:
        values = []
        for friendship in (0, 100):
            pet = PetState(friendship=friendship, updated_at=NOW)
            pet.advance(NOW + 3600)
            values.append(pet.mood)
        self.assertEqual(values[0], values[1])

    def test_sleep_rates_and_no_hardware_surcharge(self) -> None:
        outcomes = []
        for activity in (FoodActivity(), FoodActivity(1, 1)):
            pet = PetState(satiety=75, energy=40, fun=75, social=75, affection=75,
                           sleeping=True, sleep_origin="manual", updated_at=NOW)
            pet.advance(NOW + 3600, food_activity=activity)
            outcomes.append(pet.capture_checkpoint())
            for key, expected in zip(NEEDS, (73.6, 47.5, 75, 74.65, 74.75)):
                self.assertAlmostEqual(getattr(pet, key), expected)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_awake_hardware_threshold_and_caps_leave_other_needs_alone(self) -> None:
        for load, hunger, energy in ((0, 8, 3), (.3, 8, 3),
                                     (.65, 8.8, 3.25), (1, 9.6, 3.5)):
            pet = PetState(satiety=100, energy=100, fun=100, social=100,
                           affection=100, updated_at=NOW)
            for seconds in range(15, 3601, 15):
                pet.advance(NOW + seconds, food_activity=FoodActivity(load, 0))
            with self.subTest(load=load):
                self.assertAlmostEqual(pet.satiety, 100 - hunger)
                self.assertAlmostEqual(pet.energy, 100 - energy)
                self.assertAlmostEqual(pet.fun, 97)
                self.assertAlmostEqual(pet.social, 92)
                self.assertAlmostEqual(pet.affection, 94)
        food = FoodState(remaining_digest_minutes=175)
        for activity, expected in ((FoodActivity(), 94), (FoodActivity(1, 1), 92.5)):
            result = advance_food(food, 100, 1, sleeping=False, activity=activity)
            self.assertAlmostEqual(result.satiety, expected)
            self.assertEqual(result.food.remaining_digest_minutes, 115)

    def test_reserve_fade_is_independent_of_interval_partition_and_activity(self):
        food = FoodState(remaining_digest_minutes=40)
        whole = advance_food(food, 100, 1, sleeping=False)
        satiety = 100.0
        for _ in range(60):
            result = advance_food(food, satiety, 1 / 60, sleeping=False)
            food, satiety = result.food, result.satiety
        self.assertAlmostEqual(whole.satiety, 100 - 8 * 57.5 / 60)
        self.assertAlmostEqual(whole.satiety, satiety)
        busy = advance_food(FoodState(40), 100, 1, sleeping=False,
                            activity=FoodActivity(1, 1))
        self.assertEqual(busy.food.remaining_digest_minutes, 0)

    def test_long_interval_tracks_changing_needs_and_bounded_recovery(self) -> None:
        coarse = PetState(satiety=30, energy=100, fun=100, social=100,
                          affection=100, mood=80, updated_at=NOW)
        fine = PetState(satiety=30, energy=100, fun=100, social=100,
                        affection=100, mood=80, updated_at=NOW)
        coarse.advance(NOW + 4 * 3600)
        for seconds in range(5, 4 * 3600 + 1, 5):
            fine.advance(NOW + seconds)
        for key in (*NEEDS, "mood"):
            self.assertAlmostEqual(getattr(coarse, key), getattr(fine, key), delta=.05)
        self.assertEqual(coarse.satiety, 0)
        before = coarse.mood
        coarse.interact("feed", now=NOW + 4 * 3600)
        self.assertEqual(coarse.mood, before)
        coarse.advance(NOW + 4 * 3600 + 60)
        self.assertAlmostEqual(coarse.mood, before + 2)


if __name__ == "__main__":
    unittest.main()
