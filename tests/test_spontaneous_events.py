"""Regression tests for spontaneous conversations and their cooldowns."""

from __future__ import annotations

import random
import unittest
from datetime import datetime
from unittest.mock import patch

from aiko_pet.adaptive import Behaviour
from aiko_pet.dialogue import AikoMind
from aiko_pet.domain import PetState
from aiko_pet.routine import context_at


def context(hour: int = 15):
    return context_at(datetime(2026, 10, 12, hour).timestamp())


def scenario(*, mode: str = "working", duration: float = 300):
    return Behaviour(
        mode=mode, strain=45, effort=0.9,
        expected_effort=None, expectation_confident=False,
        present=True, uptime_hours=8.0,
        prolonged_work_seconds=duration,
        rest_seconds=0, can_sleep=False,
        should_wake=False, can_nap=False,
    )


class SpontaneousEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mind = AikoMind(rng=random.Random(12))

    def test_sleep_never_chooses_an_event(self) -> None:
        with patch.object(self.mind, "say_event") as speak:
            self.assertIsNone(
                self.mind.spontaneous_event(
                    PetState(sleeping=True), context(), 1000,
                ),
            )
            speak.assert_not_called()

    def test_hunger_precedes_unimportant_idle_topics(self) -> None:
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(satiety=19), context(), 1000,
            ),
            "hungry",
        )

    def test_social_cooldown_does_not_reset_early(self) -> None:
        lonely = PetState(social=15)
        first = self.mind._select_spontaneous_event(
            lonely, context(), 1000,
        )
        repeated = self.mind._select_spontaneous_event(
            lonely, context(), 1001,
        )
        self.assertEqual(first, "social_low")
        self.assertEqual(repeated, "idle")
        self.assertEqual(self.mind._last_social_comment, 1000)

    def test_affection_has_separate_cooldown_from_loneliness(self) -> None:
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(affection=15), context(), 1000,
            ),
            "affection_low",
        )
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(affection=15), context(), 1200,
            ),
            "idle",
        )

    def test_work_and_recovery_topics_depend_on_real_sessions(self) -> None:
        self.mind.situation = scenario(duration=2000)
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(), context(), 1500,
            ),
            "work_long_thought",
        )
        self.mind.situation = scenario(mode="resting")
        self.mind._last_work_duration = 2000
        self.mind._last_work_finished_at = 1450
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(), context(), 1510,
            ),
            "after_work_thought",
        )
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(), context(), 1511,
            ),
            "quiet_together",
        )

    def test_idling_uses_actual_calendar_topics(self) -> None:
        choices = {
            self.mind._choose_idle_topic(PetState(), context(15))
            for _ in range(100)
        }
        self.assertTrue(choices.issubset({"idle", "monday"}))
        self.assertIn("idle", choices)
        self.assertIn("monday", choices)


if __name__ == "__main__":
    unittest.main()
