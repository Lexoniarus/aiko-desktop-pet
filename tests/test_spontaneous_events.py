"""Regression tests for spontaneous conversations and their cooldowns."""

from __future__ import annotations

import random
import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.balance import BALANCE, parse_balance
from aiko_pet.pet.mind.adaptive_models import Behaviour
from aiko_pet.pet.mind.adaptive_policy import ActivityMode
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.dialogue_context import SituationalCondition
from aiko_pet.pet.mind.dialogue_events import DIALOGUE_EVENTS
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.dialogue_test_support import balance_source_fixture, dialogue_source_fixture


def context(hour: int = 15):
    return context_at(datetime(2026, 10, 12, hour).timestamp())


def scenario(*, mode: ActivityMode = "working", duration: float = 300):
    return Behaviour(
        mode=mode, strain=45, effort=0.9,
        expected_effort=None, expectation_confident=False,
        present=True, uptime_hours=8.0,
        prolonged_work_seconds=duration,
        rest_seconds=0,
    )


class SpontaneousEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mind = make_aiko_mind(started_at=0.0, rng=random.Random(12))

    def test_sleep_never_chooses_an_event(self) -> None:
        with patch.object(self.mind, "select_reaction") as speak:
            self.assertIsNone(
                self.mind.select_spontaneous_reaction(
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
        self.assertIsNone(repeated)
        self.assertEqual(self.mind._last_social_comment, 1000)
        interval = BALANCE.integer("mind", "social_comment_interval_seconds")
        self.assertEqual(
            self.mind._select_spontaneous_event(lonely, context(), 1000 + interval),
            "social_low",
        )

    def test_affection_has_separate_cooldown_from_loneliness(self) -> None:
        self.assertEqual(
            self.mind._select_spontaneous_event(
                PetState(affection=15), context(), 1000,
            ),
            "affection_low",
        )
        self.assertIsNone(
            self.mind._select_spontaneous_event(
                PetState(affection=15), context(), 1200,
            ),
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
        self.mind.work.last_work_duration = 2000
        self.mind.work.last_work_finished_at = 1450
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

    def test_calendar_alone_never_forces_speech_or_a_story(self) -> None:
        state = PetState()
        self.mind.clicks.append(5)
        before = state.capture_checkpoint()
        with (
            patch.object(self.mind.book, "choose") as choose,
            patch.object(self.mind.rng, "random") as chance,
        ):
            for day, hour in ((12, 8), (12, 12), (16, 20), (17, 0), (18, 15)):
                with self.subTest(day=day, hour=hour):
                    time = context_at(datetime(2026, 10, day, hour).timestamp())
                    self.assertIsNone(
                        self.mind.select_spontaneous_reaction(state, time, 1000),
                    )
            choose.assert_not_called()
            chance.assert_not_called()
        self.assertEqual(state.capture_checkpoint(), before)
        self.assertEqual(tuple(self.mind.clicks), (5,))

    def test_throttled_reminder_allows_other_real_needs_and_then_silence(self) -> None:
        state = PetState(social=15, affection=15, energy=15)
        events = [self.mind._select_spontaneous_event(state, context(), now)
                  for now in (1000, 1001, 1002)]
        self.assertEqual(events, ["social_low", "affection_low", "tired"])
        self.assertEqual(self.mind._last_social_comment, 1000)
        self.assertEqual(self.mind._last_affection_comment, 1001)
        self.assertIsNone(self.mind._select_spontaneous_event(
            PetState(social=15, affection=15), context(), 1003,
        ))

    def test_reminder_cooldown_does_not_hide_observed_rest(self) -> None:
        self.mind.situation = scenario(mode="resting")
        state = PetState(social=15)
        self.assertEqual(self.mind._select_spontaneous_event(
            state, context(), 1000,
        ), "social_low")
        self.assertEqual(self.mind._select_spontaneous_event(
            state, context(), 1001,
        ), "quiet_together")

    def test_morning_and_night_variants_require_actual_fatigue(self) -> None:
        book = self.mind.book
        lines = [line for line in book.lines
                 if line.id.startswith(("situation-morning-", "situation-night-"))]
        self.assertTrue(lines)
        for line in lines:
            hour = 8 if line.id.startswith("situation-morning-") else 0
            with self.subTest(line=line.id):
                self.assertEqual(line.event, "tired")
                self.assertTrue(all(SituationalCondition.FATIGUED in
                                    clause.situational_conditions
                                    for clause in line.conditions))
                isolated = DialogueBook((line,))
                rested = self.mind.dialogue_context(PetState(), context(hour), 10)
                self.assertIsNone(isolated.choose("tired", rested, 10))
                state = PetState(energy=5)
                # The authored relationship guard is independent of fatigue.
                snapshot = self.mind.dialogue_context(state, context(hour), 10)
                snapshot = replace(snapshot, stage=line.stages[0])
                self.assertIsNotNone(isolated.choose("tired", snapshot, 10))
                other_time = self.mind.dialogue_context(state, context(15), 10)
                self.assertIsNone(isolated.choose(
                    "tired", replace(other_time, stage=line.stages[0]), 10,
                ))
        for hour in (0, 8, 15):
            reaction = self.mind.select_spontaneous_reaction(
                PetState(energy=5), context(hour), 1000 + hour,
            )
            assert reaction is not None
            self.assertEqual(reaction.event, "tired")
            self.assertEqual(reaction.presentation, "short")

    def test_retired_speech_events_and_balance_controls_are_rejected(self) -> None:
        original = dialogue_source_fixture()["lines"][0]
        for event in ("idle", "morning", "night", "midday", "evening",
                      "monday", "friday", "weekend"):
            with self.subTest(event=event):
                self.assertNotIn(event, DIALOGUE_EVENTS)
                with self.assertRaises(ValueError):
                    Line.parse(dict(original, event=event))
        for key, value in (("spontaneous_story_probability", 0.2),
                           ("spontaneous_story_quiet_seconds", 600)):
            raw = balance_source_fixture()
            raw["dialogue"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                parse_balance(raw)


if __name__ == "__main__":
    unittest.main()
