"""Pure tests of the game-neutral fun need and aggregate mood policy."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.fun import (
    FUN_BALANCE,
    GAME_FUN_PROFILES,
    GameExperience,
    advance_fun,
    calculate_game_session_fun,
    completed_unit_reward_fraction,
)
from aiko_pet.pet.mood import (
    MoodFactors,
    advance_mood,
    calculate_mood_target,
)
from aiko_pet.pet.state import PetState


def timestamp() -> float:
    return datetime(2026, 10, 14, 8).timestamp()


class FunMoodTests(unittest.TestCase):
    def test_game_contract_is_generic_and_validated(self) -> None:
        with self.assertRaises(ValueError):
            GameExperience("any", -1)
        with self.assertRaises(ValueError):
            GameExperience("any", 2, successful_units=3)
        with self.assertRaises(ValueError):
            GameExperience("any", 1, neutral_units=True)  # type: ignore[arg-type]
        self.assertIn("rock_paper_scissors", GAME_FUN_PROFILES)
        self.assertEqual(
            calculate_game_session_fun(GameExperience("any", 0), 30).fun_points,
            0,
        )

    def test_an_unplayed_window_has_no_effect(self) -> None:
        pet = PetState(fun=27, updated_at=timestamp())
        before = encode_pet_state(pet)
        self.assertEqual(
            pet.record_game_experience(
                GameExperience("rock_paper_scissors", 0), now=timestamp(),
            ),
            0.0,
        )
        self.assertEqual(encode_pet_state(pet), before)

    def test_aiko_wins_a_little_more_but_losses_are_still_fun(self) -> None:
        won = calculate_game_session_fun(
            GameExperience("rock_paper_scissors", 2, successful_units=2),
            30,
        )
        lost = calculate_game_session_fun(
            GameExperience("rock_paper_scissors", 2, setback_units=2),
            30,
        )
        self.assertGreater(won.fun_points, lost.fun_points)
        self.assertGreater(lost.fun_points, 0)
        self.assertEqual(won.energy_cost, 1)
        self.assertGreater(won.social_gain, 0)

    def test_many_completed_units_have_diminishing_returns(self) -> None:
        self.assertEqual(completed_unit_reward_fraction(2), 1.0)
        self.assertLess(completed_unit_reward_fraction(8), 1.0)
        reward = calculate_game_session_fun(
            GameExperience("rock_paper_scissors", 100, successful_units=100),
            20,
        )
        self.assertLessEqual(
            reward.fun_points, FUN_BALANCE.maximum_fun_gain_per_session,
        )

    def test_fun_declines_only_with_simulated_awake_time(self) -> None:
        self.assertAlmostEqual(advance_fun(75, 16, sleeping=False), 33.4)
        self.assertEqual(advance_fun(75, 8, sleeping=True), 75)
        self.assertEqual(advance_fun(75, 0, sleeping=False), 75)

    def test_four_short_sessions_balanced_across_one_awake_day(self) -> None:
        start = timestamp()
        pet = PetState(updated_at=start, fun=70)
        for hour in range(16):
            if hour in (1, 5, 9, 13):
                pet.record_game_experience(
                    GameExperience(
                        "rock_paper_scissors", 2,
                        successful_units=1, setback_units=1,
                    ),
                    now=start + hour * 3600,
                )
            pet.advance(
                start + (hour + 1) * 3600,
                auto_routine=False, elapsed_seconds=3600,
            )
        self.assertGreater(pet.fun, 60)
        self.assertLess(pet.fun, 90)

    def test_mood_responds_to_all_needs_and_friendship(self) -> None:
        normal = MoodFactors(75, 75, 75, 75, 75)
        self.assertAlmostEqual(calculate_mood_target(normal), 75.0)
        for key in ("satiety", "energy", "fun", "social", "affection"):
            with self.subTest(need=key):
                modified = {name: 75.0 for name in (
                    "satiety", "energy", "fun", "social", "affection",
                )}
                modified[key] = 10
                self.assertLess(
                    calculate_mood_target(MoodFactors(**modified)), 75,
                )
        self.assertGreater(
            calculate_mood_target(MoodFactors(75, 75, 75, 75, 75, 100)),
            75,
        )

    def test_mood_is_smoothed_and_never_changes_fun(self) -> None:
        start = timestamp()
        low_mood = PetState(
            mood=15, fun=60, energy=65, updated_at=start,
        )
        high_mood = PetState(
            mood=90, fun=60, energy=65, updated_at=start,
        )
        low_mood.advance(start + 3600, elapsed_seconds=3600)
        high_mood.advance(start + 3600, elapsed_seconds=3600)
        self.assertEqual(low_mood.fun, high_mood.fun)
        self.assertGreater(low_mood.mood, 15)
        self.assertLess(high_mood.mood, 90)
        self.assertAlmostEqual(
            advance_mood(75, 20, 0, sleeping=False), 75,
        )

    def test_old_saves_keep_mood_and_default_fun_safely(self) -> None:
        old = decode_pet_state({"mood": 34}, now=timestamp())
        self.assertEqual(old.fun, 75)
        self.assertEqual(old.mood, 34)
        corrupt = decode_pet_state({"fun": float("nan")}, now=timestamp())
        self.assertEqual(corrupt.fun, 75)
        restored = decode_pet_state(encode_pet_state(old), now=timestamp())
        self.assertEqual(restored.fun, old.fun)
        self.assertEqual(restored.mood, old.mood)
        self.assertNotIn("game_score", encode_pet_state(restored))


if __name__ == "__main__":
    unittest.main()
