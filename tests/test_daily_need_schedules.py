"""Historical care schedules retain their need/mood baseline, not reward plateaus."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.pet.care_result import CareEffect
from aiko_pet.pet.food import FoodActivity, FoodId
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.state import PetState

START = datetime(2026, 10, 12, 7).timestamp()
NEEDS = ("satiety", "energy", "fun", "social", "affection")
SCHEDULES: tuple[tuple[tuple[int, tuple[str, ...]], ...], ...] = (
    (
        (0, ("onigiri", "talk")),
        (150, ("talk", "game")),
        (300, ("sandwich", "pet")),
        (450, ("talk", "game", "pet")),
        (600, ("apple", "talk")),
        (720, ("sandwich", "pet")),
        (840, ("talk", "game")),
        (960, ("dorayaki", "pet", "sleep")),
    ),
    (
        (0, ("onigiri", "talk", "pet", "game")),
        (360, ("sandwich", "apple", "talk", "talk", "pet", "game")),
        (720, ("sandwich", "talk", "pet", "game")),
        (960, ("dorayaki", "talk", "pet", "sleep")),
    ),
)
FOODS: dict[str, FoodId] = {
    "onigiri": "onigiri", "sandwich": "sandwich",
    "apple": "apple", "dorayaki": "dorayaki",
}


class DailyNeedScheduleTests(unittest.TestCase):
    def test_settled_eight_and_four_phase_days_preserve_needs_and_mood(self) -> None:
        expectations = (
            ((57.5, 42.5, 80.5, 63, 67), (57.14, 77.93)),
            ((51.9, 42.5, 82, 50.8, 53), (47.79, 79.14)),
        )
        for schedule, (expected_needs, expected_mood) in zip(SCHEDULES, expectations):
            with self.subTest(phases=len(schedule)):
                pet = PetState(
                    satiety=100, energy=100, fun=100, social=100,
                    affection=100, mood=80, updated_at=START,
                    friendship=95 if len(schedule) == 8 else 70,
                )
                minima = [100.0] * 5
                mood_min, mood_max = 100.0, 0.0
                accepted = 0
                for day in range(8):
                    day_start = START + day * 86400
                    if pet.sleeping:
                        pet.interact("sleep", now=day_start)
                    actions = dict(schedule)
                    for seconds in range(0, 86401, 15):
                        stamp = day_start + seconds
                        if seconds:
                            pet.advance(stamp, food_activity=FoodActivity(.2, .5))
                        if day == 7:
                            minima = [min(low, getattr(pet, key))
                                      for low, key in zip(minima, NEEDS)]
                            mood_min, mood_max = min(mood_min, pet.mood), max(
                                mood_max, pet.mood,
                            )
                        due = (
                            actions.get(seconds // 60, ()) if seconds % 60 == 0 else ()
                        )
                        for action in due:
                            if action == "game":
                                pet.record_game_experience(
                                    GameExperience("rock_paper_scissors", 3), now=stamp,
                                )
                            elif action in FOODS:
                                result = pet.interact(
                                    "feed", food_id=FOODS[action], now=stamp,
                                )
                                if day == 7:
                                    self.assertNotEqual(
                                        result.effect, CareEffect.FOOD_SATISFIED,
                                    )
                                    accepted += 1
                            else:
                                pet.interact(action, now=stamp)
                # These schedules do not generate wishes or their impressions.
                # They are not acceptance scenarios for relationship balance.
                self.assertIsNotNone(pet.friendship_history.continuous_since)
                self.assertIsNotNone(pet.friendship_history.last_contact)
                self.assertEqual(pet.friendship_history.critical, ())
                self.assertEqual(pet.friendship_history.rewards, ())
                self.assertEqual(accepted, 5)
                self.assertFalse(pet.sleeping)
                self.assertEqual(pet.energy, 100)
                for key, actual, expected in zip(NEEDS, minima, expected_needs):
                    with self.subTest(need=key):
                        self.assertGreater(actual, 40)
                        self.assertAlmostEqual(actual, expected, delta=.1)
                self.assertAlmostEqual(mood_min, expected_mood[0], delta=.1)
                self.assertAlmostEqual(mood_max, expected_mood[1], delta=.1)


if __name__ == "__main__":
    unittest.main()
