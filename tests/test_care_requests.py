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
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from tools.pet_test_support import set_test_pet_values


class Monitor:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()


class CareRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState(satiety=100, mood=100, fun=100, social=100, affection=100)
        self.settings, self.mind = PetSettings(), make_aiko_mind(started_at=0.0)
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

    def test_wish_willingness_reads_do_not_spend_tolerated_extra_strokes(self):
        set_test_pet_values(self.state, friendship=0, affection=60)
        before = self.state.capture_checkpoint()
        for _ in range(4):
            self.assertFalse(self.attention.wish_context().petting_welcome)
        self.assertEqual(self.state.capture_checkpoint(), before)
        self.state.interact("pet")
        self.assertEqual(self.state.moodlets.interactions.petting_excess_attempts, 1)
        set_test_pet_values(self.state, affection=59)
        self.assertTrue(self.attention.wish_context().petting_welcome)

    def test_threshold_and_all_tie_breaks(self) -> None:
        self.assertIsNone(choose_care_request(self.state))
        set_test_pet_values(self.state, satiety=70)
        self.assertEqual(choose_care_request(self.state), 'care_request_feed')
        set_test_pet_values(self.state, social=60, affection=60, fun=60)
        self.assertEqual(choose_care_request(self.state), 'care_request_talk')
        set_test_pet_values(self.state, social=100)
        self.assertEqual(choose_care_request(self.state), 'care_request_pet')
        set_test_pet_values(self.state, affection=100)
        self.assertEqual(choose_care_request(self.state), 'care_request_play')
        set_test_pet_values(self.state, sleeping=True)
        self.assertIsNone(choose_care_request(self.state))

    def test_request_is_authored_and_throttled_for_thirty_minutes(self) -> None:
        set_test_pet_values(self.state, satiety=70)
        first = self.attention.spontaneous(1000, self.context)
        self.assertTrue(first.due)
        self.assertIsNotNone(first.reaction)
        self.assertFalse(self.attention.spontaneous(
            2799, self.context,
        ).due)
        self.assertTrue(self.attention.spontaneous(
            2800, self.context,
        ).due)

    def test_accepted_care_has_three_minute_grace(self) -> None:
        set_test_pet_values(self.state, satiety=60)
        self.mind.record_accepted_care('pet', 1000)
        self.assertFalse(self.attention.spontaneous(
            1179, self.context,
        ).due)
        self.assertTrue(self.attention.spontaneous(
            1180, self.context,
        ).due)

    def test_visible_ui_and_running_reactions_are_not_interrupted(self) -> None:
        set_test_pet_values(self.state, satiety=60)
        for flag in ('bubble_visible',):
            with self.subTest(flag=flag):
                arguments = {flag: True}
                self.assertFalse(self.attention.spontaneous(
                    1000, self.context, **arguments,
                ).due)
        self.assertFalse(self.attention.spontaneous(
            1000, self.context, action_until=1001,
        ).due)
        self.settings.spontaneous_talk = False
        self.assertFalse(self.attention.spontaneous(
            1000, self.context,
        ).due)
        self.assertEqual(self.attention.next_care_request, 0)
