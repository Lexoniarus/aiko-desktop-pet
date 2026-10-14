"""Application-level game adapters, integration and transient score checks."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.controller import CareController, CareRuntime
from aiko_pet.application.game_experience import (
    GameExperienceCoordinator, experience_from_rock_paper_scissors,
)
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.games.rock_paper_scissors import Score
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.mind import PetMind
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.state import PetState


def timestamp() -> float:
    return datetime(2026, 10, 14, 12).timestamp()


class GameExperienceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState(fun=35, updated_at=timestamp())
        self.mind = PetMind()
        self.adaptive = AdaptiveRoutine()
        clock = ActiveSessionClock(lambda: 100.0)
        self.router = ApplicationRouter(
            CareController(
                self.state, self.mind, self.adaptive, clock=clock,
            ),
            game_experience=GameExperienceCoordinator(
                self.state, self.mind, self.adaptive, clock=clock,
            ),
        )
        self.runtime = CareRuntime(
            wall_time=timestamp(), monotonic_time=100.0,
            auto_routine=False, allow_bedtime=None, allow_nap=False,
            interrupt_nap=False, effort=None,
        )

    def test_rps_score_orientation_is_aikos_not_players(self) -> None:
        experience = experience_from_rock_paper_scissors(
            Score(wins=3, losses=1, draws=2),
        )
        self.assertEqual(experience.completed_units, 6)
        self.assertEqual(experience.successful_units, 1)
        self.assertEqual(experience.setback_units, 3)
        self.assertEqual(experience.neutral_units, 2)

    def test_completed_game_updates_fun_only_once(self) -> None:
        score = Score(wins=1, losses=2, draws=1)
        outcome = self.router.complete_game(
            experience_from_rock_paper_scissors(score), runtime=self.runtime,
        )
        self.assertGreater(outcome.fun_gained, 0)
        self.assertEqual(self.state.fun, outcome.fun_after)
        self.assertGreater(self.state.social, 75)
        self.assertLess(self.state.energy, 75)
        self.assertGreater(self.state.friendship, 15)
        saved = self.state.to_dict()
        self.assertNotIn("score", saved)
        self.assertNotIn("completed_units", saved)
        self.assertNotIn("game_id", saved)

    def test_empty_game_cannot_farm_fun_or_friendship(self) -> None:
        original = self.state.to_dict()
        result = self.router.complete_game(
            experience_from_rock_paper_scissors(Score()),
            runtime=self.runtime,
        )
        self.assertEqual(result.fun_gained, 0)
        self.assertEqual(self.state.to_dict(), original)

    def test_future_game_needs_only_a_profile_not_new_calculator(self) -> None:
        # There is intentionally no RPS dependency in the general fun domain.
        from aiko_pet.pet.fun import GAME_FUN_PROFILES, GameFunProfile

        GAME_FUN_PROFILES["test_quiz"] = GameFunProfile(
            4.0, 1.0, 0.0, 0.0, 0.2, 0.3,
        )
        try:
            outcome = self.router.complete_game(
                GameExperience("test_quiz", 3, successful_units=2),
                runtime=self.runtime,
            )
            self.assertGreater(outcome.fun_gained, 0)
        finally:
            del GAME_FUN_PROFILES["test_quiz"]


if __name__ == "__main__":
    unittest.main()
