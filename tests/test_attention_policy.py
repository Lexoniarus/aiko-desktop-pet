"""Attention policy is usable without a desktop display or API listener."""

from __future__ import annotations

import random
import unittest
from unittest.mock import patch

from aiko_pet.adaptive import AdaptiveRoutine
from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.commands import NotificationCommand
from aiko_pet.application.controller import CareController
from aiko_pet.application.events import IncomingNotification
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.dialogue import AikoMind, ComputerVoice
from aiko_pet.domain import PetState
from aiko_pet.routine import context_at
from aiko_pet.storage import PetSettings
from aiko_pet.system_activity import ComputerSnapshot


class StaticReadings:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()


class AttentionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState()
        self.settings = PetSettings()
        self.mind = AikoMind(rng=random.Random(7))
        self.voice = ComputerVoice(rng=random.Random(8))
        self.router = ApplicationRouter(
            CareController(self.state, self.mind, AdaptiveRoutine()),
        )
        self.attention = AttentionCoordinator(
            self.state, self.settings, self.mind, self.voice,
            StaticReadings(), self.router, started_at=100.0,
        )

    def test_commentary_has_own_cooldown(self) -> None:
        self.assertGreaterEqual(self.attention.next_comment, 280.0)
        self.assertLessEqual(self.attention.next_comment, 460.0)
        self.attention.mark_spoken(200.0)
        self.assertFalse(self.attention.should_greet(214.0))
        self.assertTrue(self.attention.should_greet(215.0))
        self.settings.spontaneous_talk = False
        self.assertFalse(self.attention.should_greet(999.0))

    def test_silent_dialogue_slot_is_distinct_from_not_due(self) -> None:
        self.attention.next_comment = 199.0
        self.attention.last_spoken = -1000.0
        with (
            patch.object(self.voice, "maybe_event", return_value=None),
            patch.object(self.mind, "spontaneous_event", return_value=None),
        ):
            result = self.attention.spontaneous(
                200.0, context_at(1_781_000_000), toolbar_visible=False,
            )
        self.assertTrue(result.due)
        self.assertIsNone(result.reaction)
        self.assertFalse(self.attention.spontaneous(
            201.0, context_at(1_781_000_000), toolbar_visible=False,
        ).due)

    def test_idles_never_interrupt_sleep_or_toolbar(self) -> None:
        self.attention.next_idle_emote = 0
        self.state.sleeping = True
        self.assertIsNone(self.attention.idle_animation(
            200, action_until=0, walking=False, toolbar_visible=False,
        ))
        self.state.sleeping = False
        self.attention.next_idle_emote = 0
        self.assertIsNone(self.attention.idle_animation(
            201, action_until=0, walking=False, toolbar_visible=True,
        ))
        self.attention.next_idle_emote = 0
        with patch(
            "aiko_pet.application.attention.random.choice",
            return_value="review",
        ):
            self.assertEqual(self.attention.idle_animation(
                202, action_until=0, walking=False, toolbar_visible=False,
            ), "review")

    def test_notification_remains_queued_during_visible_dialogue(self) -> None:
        notice = IncomingNotification(
            event_id="a", source="browser", title="Termin",
            message="Gleich beginnt es.",
        )
        self.router.dispatch(NotificationCommand(notice))
        self.assertIsNone(self.attention.next_notification(
            300, action_until=0, bubble_visible=True,
            popup_visible=False, toolbar_visible=False,
        ))
        self.assertIsNone(self.attention.next_notification(
            300, action_until=0, bubble_visible=False,
            popup_visible=False, toolbar_visible=True,
        ))
        self.assertEqual(self.attention.next_notification(
            300, action_until=0, bubble_visible=False,
            popup_visible=False, toolbar_visible=False,
        ), notice)
        self.assertIsNone(self.attention.next_notification(
            300, action_until=0, bubble_visible=False,
            popup_visible=False, toolbar_visible=False,
        ))


if __name__ == "__main__":
    unittest.main()
