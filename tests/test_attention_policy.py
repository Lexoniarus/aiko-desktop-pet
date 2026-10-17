"""Attention policy is usable without a desktop display or API listener."""

from __future__ import annotations
from tools.pet_test_support import set_test_pet_values

import random
import unittest
from unittest.mock import patch

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.commands import NotificationCommand
from aiko_pet.application.controller import CareController
from aiko_pet.application.events import IncomingNotification
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot


class StaticReadings:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()


class AttentionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState()
        self.settings = PetSettings()
        self.mind = make_aiko_mind(started_at=0.0, rng=random.Random(7))
        self.workload_events = WorkloadEventDetector(rng=random.Random(8))
        self.router = ApplicationRouter(
            CareController(self.state, self.mind, AdaptiveRoutine(),
                           clock=ActiveSessionClock(lambda: 0.0)),
        )
        self.attention = AttentionCoordinator(
            self.state, self.settings, self.mind, self.workload_events,
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
            patch.object(self.workload_events, "maybe_event", return_value=None),
            patch.object(self.mind, "select_spontaneous_reaction", return_value=None),
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
        set_test_pet_values(self.state, sleeping=True)
        self.assertIsNone(self.attention.select_idle_animation(
            200, action_until=0, walking=False, toolbar_visible=False,
        ))
        set_test_pet_values(self.state, sleeping=False)
        self.attention.next_idle_emote = 0
        self.assertIsNone(self.attention.select_idle_animation(
            201, action_until=0, walking=False, toolbar_visible=True,
        ))
        self.attention.next_idle_emote = 0
        with patch(
            "aiko_pet.application.attention.random.choice",
            return_value="review",
        ):
            self.assertEqual(self.attention.select_idle_animation(
                202, action_until=0, walking=False, toolbar_visible=False,
            ), "review")

    def test_cursor_comment_cooldown_and_proximity(self) -> None:
        self.attention.next_cursor_line = 0.0
        self.attention.last_spoken = -1000.0
        with (
            patch("aiko_pet.application.attention.random.random", return_value=0.01),
            patch("aiko_pet.application.attention.random.uniform", return_value=300.0),
        ):
            self.assertEqual(self.attention.select_cursor_comment_event(
                800.0, 1000, 1000.0, toolbar_visible=False,
            ), "cursor_far")
            self.assertEqual(self.attention.next_cursor_line, 1300.0)
            self.assertIsNone(self.attention.select_cursor_comment_event(
                100.0, 1000, 1299.0, toolbar_visible=False,
            ))
            self.assertEqual(self.attention.select_cursor_comment_event(
                100.0, 1000, 1300.0, toolbar_visible=False,
            ), "cursor_follow")

    def test_cursor_silence_respects_character_hover_and_settings(self) -> None:
        self.attention.next_cursor_line = 0.0
        self.attention.last_spoken = 900.0
        with patch("aiko_pet.application.attention.random.random") as chance:
            self.assertIsNone(self.attention.select_cursor_comment_event(
                800.0, 1000, 1000.0, toolbar_visible=False,
            ))
            self.attention.last_spoken = -1000.0
            self.assertIsNone(self.attention.select_cursor_comment_event(
                800.0, 1000, 1000.0, toolbar_visible=True,
            ))
            self.settings.follow_cursor = False
            self.assertIsNone(self.attention.select_cursor_comment_event(
                800.0, 1000, 1000.0, toolbar_visible=False,
            ))
            self.settings.follow_cursor = True
            self.settings.spontaneous_talk = False
            self.assertIsNone(self.attention.select_cursor_comment_event(
                800.0, 1000, 1000.0, toolbar_visible=False,
            ))
            self.settings.spontaneous_talk = True
            set_test_pet_values(self.state, sleeping=True)
            self.assertIsNone(self.attention.select_cursor_comment_event(
                800.0, 1000, 1000.0, toolbar_visible=False,
            ))
            chance.assert_not_called()
        self.assertEqual(self.attention.next_cursor_line, 0.0)

    def test_walk_comment_only_when_spontaneous_and_quiet_enough(self) -> None:
        self.attention.last_spoken = 870.0
        with patch(
            "aiko_pet.application.attention.random.random", return_value=0.01,
        ) as chance:
            self.assertFalse(self.attention.should_comment_after_walk(1000.0))
            chance.assert_not_called()
            self.attention.last_spoken = 869.0
            self.assertTrue(self.attention.should_comment_after_walk(1000.0))
            self.settings.spontaneous_talk = False
            self.assertFalse(self.attention.should_comment_after_walk(1000.0))

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
