"""User contact coordinates mind decisions without importing Tk."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from aiko_pet.application.contact import ContactCoordinator, ContactPorts
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class ContactCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState()
        self.mind = make_aiko_mind(started_at=0.0)
        self.adaptive = AdaptiveRoutine()
        self.hover = Mock()
        self.interrupt = Mock()
        self.show = Mock()
        self.cancel = Mock()
        self.hide = Mock()
        self.wake = Mock()
        self.reactions: list[tuple[Reaction | None, int]] = []
        self.greet_enabled = True
        self.foreground = self.playback = False
        self.game = self.story = False
        self.event: str | None = None
        self.context = context_at(datetime(2026, 10, 12, 13).timestamp())
        self.contact = ContactCoordinator(
            state=self.state,
            mind=self.mind,
            adaptive=self.adaptive,
            ports=ContactPorts(
                context=lambda: self.context,
                toolbar_hidden=lambda: True,
                mark_hover=self.hover,
                interrupt_walk=self.interrupt,
                show_toolbar=self.show,
                game_open=lambda: self.game,
                cancel_followup=self.cancel,
                hide_speech=self.hide,
                react=lambda reaction, duration: self.reactions.append(
                    (reaction, duration),
                ),
                should_greet=lambda _now: self.greet_enabled,
                foreground_active=lambda: self.foreground,
                playback_active=lambda: self.playback,
                story_active=lambda: self.story,
                reaction_event=lambda: self.event,
                wake_from_clicks=self.wake,
            ),
        )

    def test_hover_opens_toolbar_and_interrupts_walk(self) -> None:
        with patch.object(self.mind, "return_to_pet", return_value=None):
            self.contact.enter()
        self.hover.assert_called_once()
        self.interrupt.assert_called_once()
        self.show.assert_called_once()
        self.assertEqual(self.reactions, [(None, 2800)])

    def test_petting_refusal_is_semantic_and_playback_blocks_only_until_finished(self):
        set_test_pet_values(self.state, affection=100)
        for _ in range(3):
            self.state.interact("pet")
        self.contact.note_text("pet_refused")
        self.state.interact("pet")
        before = self.state.capture_checkpoint()
        self.playback = True
        self.assertFalse(self.contact.can_interact("pet"))
        self.playback = False
        for _ in range(4):
            self.assertTrue(self.contact.can_interact("pet"))
        self.assertEqual(self.state.capture_checkpoint(), before)

    def test_hover_greeting_and_ui_contact_do_not_renew_durable_care(self) -> None:
        history = self.state.friendship_history
        self.contact.enter()
        self.contact.greet()
        self.contact.record_contact(1000)
        self.contact.click("left")
        self.assertEqual(self.state.friendship_history, history)

    def test_busy_hover_only_opens_ui_and_busy_playback_ignores_clicks(self) -> None:
        for owner in ("foreground", "playback"):
            with self.subTest(owner=owner):
                self.foreground = owner == "foreground"
                self.playback = owner == "playback"
                self.assertFalse(self.contact.can_interact("pet"))
                self.contact.enter()
                self.interrupt.assert_not_called()
                self.assertEqual(self.reactions, [])
                self.assertEqual(list(self.mind.clicks), [])
        self.assertEqual(self.show.call_count, 2)
        self.contact.click("right")
        self.assertEqual(list(self.mind.clicks), [])
        self.assertEqual(self.reactions, [])
        self.foreground = self.playback = False
        self.assertTrue(self.contact.can_interact("pet"))

    def test_click_preserves_mind_event_and_adaptive_contact(self) -> None:
        reaction = Reaction("test-click", (Cue.text("Hallo"),), "idle", "click_left")
        with (
            patch.object(self.mind, "return_to_pet", return_value=None),
            patch.object(self.mind, "click", return_value=reaction) as choose,
            patch.object(self.adaptive, "note_interaction") as noted,
        ):
            self.contact.click("left")
        choose.assert_called_once()
        noted.assert_called_once()
        self.assertEqual(self.reactions[-1], (reaction, 2800))

    def test_click_replies_allow_escalation_without_unlocking_care(self) -> None:
        self.playback = True
        for index, event in enumerate(("click_left", "click_right", "click_notice",
                                       "rapid_click")):
            self.event = event
            self.assertFalse(self.contact.can_interact("pet"))
            self.assertFalse(self.contact.can_interact("play"))
            with patch("aiko_pet.application.contact.time.monotonic",
                       return_value=1000 + index / 10):
                self.contact.click("left" if index % 2 == 0 else "right")
        self.assertEqual(len(self.mind.clicks), 4)
        self.assertGreater(self.mind.irritation_reaction_until, 1000.3)
        reaction = self.reactions[-1][0]
        assert reaction is not None
        self.assertEqual(reaction.event, "rapid_click")

    def test_other_playback_never_admits_teasing_clicks(self) -> None:
        self.playback = True
        for event in (None, "care_pet", "care_talk", "object_recognized",
                      "game_greeting", "greeting"):
            with self.subTest(event=event):
                self.event = event
                self.contact.click("left")
                self.contact.click("right")
        self.assertEqual(list(self.mind.clicks), [])
        self.assertEqual(self.reactions, [])

    def test_game_and_story_take_priority_over_click_feedback(self) -> None:
        self.playback, self.event = True, "click_left"
        for blocked in ("game", "story"):
            with self.subTest(blocked=blocked):
                self.game = blocked == "game"
                self.story = blocked == "story"
                self.contact.click("left")
                self.contact.click("right")
        self.assertEqual(list(self.mind.clicks), [])
        self.assertEqual(self.reactions, [])

    def test_sleep_replies_remain_interruptible_until_fourth_click_wakes(self) -> None:
        set_test_pet_values(self.state, sleeping=True)
        self.playback, self.event = True, "sleep"
        for count in range(1, 5):
            with patch("aiko_pet.application.contact.time.monotonic",
                       return_value=1000 + count / 10):
                self.contact.click("left" if count % 2 else "right")
            if count < 4:
                reaction = self.reactions[-1][0]
                assert reaction is not None
                self.assertEqual(reaction.event, "sleep_click")
                self.event = reaction.event
                self.wake.assert_not_called()
        self.wake.assert_called_once_with()
        self.assertEqual(len(self.reactions), 3)
        self.assertFalse(self.contact.can_interact("pet"))
        self.assertTrue(self.contact.can_interact("sleep"))

    def test_sleep_does_not_admit_clicks_during_unrelated_playback(self) -> None:
        set_test_pet_values(self.state, sleeping=True)
        self.playback, self.event = True, "care_pet"
        self.contact.click("left")
        self.assertEqual(list(self.mind.clicks), [])
        self.wake.assert_not_called()

    def test_no_reaction_hides_old_speech_and_cancels_followup(self) -> None:
        self.contact.react_to_click(None)
        self.cancel.assert_called_once()
        self.hide.assert_called_once()

    def test_three_clicks_suppress_duplicated_emote(self) -> None:
        self.mind.clicks.extend((1.0, 2.0, 3.0))
        reaction = Reaction(
            "test-click",
            (
                Cue("emote", "heart", 700),
                Cue.text("Hallo"),
            ),
            "idle",
            "click_left",
        )
        self.contact.react_to_click(reaction)
        chosen, duration = self.reactions[-1]
        assert chosen is not None
        self.assertEqual(chosen.beats[0].kind, "text")
        self.assertEqual(duration, 2800)
        self.assertEqual(reaction.beats[0].content, "heart")

    def test_greeting_is_guarded_by_attention_policy(self) -> None:
        self.greet_enabled = False
        self.contact.greet()
        self.assertEqual(self.reactions, [])
