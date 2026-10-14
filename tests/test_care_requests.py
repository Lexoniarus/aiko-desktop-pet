"""Moderate needs, friendly authored requests and non-interrupting cooldowns."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.care_requests import choose_care_request
from aiko_pet.application.controller import CareController
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.application.settings import PetSettings
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.mind import PetMind
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot


class Monitor:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()


class CareRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState(satiety=100, mood=100, fun=100, social=100, affection=100)
        self.settings, self.mind = PetSettings(), PetMind()
        router = ApplicationRouter(CareController(
            self.state, self.mind, AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0.),
        ))
        self.attention = AttentionCoordinator(
            self.state, self.settings, self.mind, WorkloadEventDetector(),
            Monitor(), router, started_at=0,
        )
        self.attention.next_comment = float('inf')
        self.context = context_at(datetime(2026, 10, 13, 12).timestamp())

    def test_threshold_and_all_tie_breaks(self) -> None:
        self.assertIsNone(choose_care_request(self.state))
        self.state.satiety = 70
        self.assertEqual(choose_care_request(self.state), 'care_request_feed')
        self.state.social = self.state.affection = self.state.fun = 60
        self.assertEqual(choose_care_request(self.state), 'care_request_talk')
        self.state.social = 100
        self.assertEqual(choose_care_request(self.state), 'care_request_pet')
        self.state.affection = 100
        self.assertEqual(choose_care_request(self.state), 'care_request_play')
        self.state.sleeping = True
        self.assertIsNone(choose_care_request(self.state))

    def test_request_is_authored_and_throttled_for_thirty_minutes(self) -> None:
        self.state.satiety = 70
        first = self.attention.spontaneous(1000, self.context, toolbar_visible=False)
        self.assertTrue(first.due)
        self.assertIsNotNone(first.reaction)
        self.assertFalse(self.attention.spontaneous(
            2799, self.context, toolbar_visible=False,
        ).due)
        self.assertTrue(self.attention.spontaneous(
            2800, self.context, toolbar_visible=False,
        ).due)

    def test_accepted_care_has_three_minute_grace(self) -> None:
        self.state.satiety = 60
        self.mind.after_care('pet', 1000)
        self.assertFalse(self.attention.spontaneous(
            1179, self.context, toolbar_visible=False,
        ).due)
        self.assertTrue(self.attention.spontaneous(
            1180, self.context, toolbar_visible=False,
        ).due)

    def test_visible_ui_and_running_reactions_are_not_interrupted(self) -> None:
        self.state.satiety = 60
        for flag in ('toolbar_visible', 'bubble_visible', 'popup_visible'):
            with self.subTest(flag=flag):
                arguments = {flag: True}
                self.assertFalse(self.attention.spontaneous(
                    1000, self.context, **{'toolbar_visible': False, **arguments},
                ).due)
        self.assertFalse(self.attention.spontaneous(
            1000, self.context, toolbar_visible=False, action_until=1001,
        ).due)
        self.settings.spontaneous_talk = False
        self.assertFalse(self.attention.spontaneous(
            1000, self.context, toolbar_visible=False,
        ).due)
        self.assertEqual(self.attention.next_care_request, 0)
