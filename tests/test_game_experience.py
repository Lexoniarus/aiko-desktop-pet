"""Application-level game adapters, integration and transient score checks."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.controller import CareController
from aiko_pet.application.game_experience import (
    GameExperienceCoordinator,
    experience_from_rock_paper_scissors,
    experience_from_session,
)
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.games.contracts import GameId, SessionSummary
from aiko_pet.games.rock_paper_scissors import Score
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState


def timestamp() -> float:
    return datetime(2026, 10, 14, 12).timestamp()


class GameExperienceTests(unittest.TestCase):
    def test_shared_summary_preserves_orientation_for_each_game(self) -> None:
        for game in GameId:
            result = experience_from_session(SessionSummary(game, 2, 1, 3))
            self.assertEqual(result.game_id, game.value)
            self.assertEqual(result.completed_units, 6)
            self.assertEqual(result.successful_units, 1)
            self.assertEqual(result.setback_units, 2)

    def test_summary_rejects_invalid_counts(self) -> None:
        with self.assertRaises(ValueError):
            SessionSummary(GameId.BLACKJACK, wins=-1)

    def setUp(self) -> None:
        self.state = PetState(fun=35, updated_at=timestamp())
        self.mind = make_aiko_mind(started_at=0.0)
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
        self.runtime = SessionInputs(
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
            experience_from_rock_paper_scissors(score), inputs=self.runtime,
        )
        self.assertGreater(outcome.fun_gained, 0)
        self.assertEqual(self.state.fun, outcome.fun_after)
        self.assertGreater(self.state.social, 75)
        self.assertLess(self.state.energy, 75)
        self.assertEqual(self.state.friendship, 15)
        saved = encode_pet_state(self.state)
        self.assertNotIn("score", saved)
        self.assertNotIn("completed_units", saved)
        self.assertNotIn("game_id", saved)

    def test_empty_game_cannot_farm_fun_or_friendship(self) -> None:
        original = encode_pet_state(self.state)
        result = self.router.complete_game(
            experience_from_rock_paper_scissors(Score()),
            inputs=self.runtime,
        )
        self.assertEqual(result.fun_gained, 0)
        self.assertEqual(encode_pet_state(self.state), original)

    def test_tic_tac_toe_uses_explicit_profile_and_generic_completion(self) -> None:
        from aiko_pet.pet.fun import GAME_FUN_PROFILES

        self.assertGreater(
            GAME_FUN_PROFILES["tic_tac_toe"].base_fun_per_completed_unit,
            GAME_FUN_PROFILES["rock_paper_scissors"].base_fun_per_completed_unit,
        )
        outcome = self.router.complete_game(
            experience_from_session(SessionSummary(GameId.TIC_TAC_TOE, wins=1)),
            inputs=self.runtime,
        )
        self.assertGreater(outcome.fun_gained, 0)

    def test_future_game_needs_only_a_profile_not_new_calculator(self) -> None:
        # There is intentionally no RPS dependency in the general fun domain.
        from aiko_pet.pet.fun import GAME_FUN_PROFILES, GameFunProfile

        GAME_FUN_PROFILES["test_quiz"] = GameFunProfile(
            4.0, 0.2, 0.3,
        )
        try:
            outcome = self.router.complete_game(
                GameExperience("test_quiz", 3, successful_units=2),
                inputs=self.runtime,
            )
            self.assertGreater(outcome.fun_gained, 0)
        finally:
            del GAME_FUN_PROFILES["test_quiz"]


if __name__ == "__main__":
    unittest.main()
