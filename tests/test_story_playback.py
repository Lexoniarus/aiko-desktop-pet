"""Reading clicks are presentation controls, not pet-care or teasing actions."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from aiko_pet.application.contact import ContactCoordinator, ContactPorts
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer


class StoryPlaybackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.callbacks: dict[str, object] = {}
        self.index = 0
        self.rendered: list[str] = []
        self.hidden = Mock()

        def schedule(_delay: int, callback: object) -> str:
            self.index += 1
            token = str(self.index)
            self.callbacks[token] = callback
            return token

        def cancel(token: str) -> None:
            self.callbacks.pop(token, None)

        self.player = ReactionPlayer(
            schedule=schedule,
            cancel_timer=cancel,
            display_emote=lambda s, _d: self.rendered.append(s),
            display_text=lambda s, _d: self.rendered.append(s),
            start_action=lambda _s, _d: None,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
            hide_speech=self.hidden,
        )
        self.story = Reaction(
            "story",
            (
                Cue("emote", "question", 800),
                Cue.text("Anfang."),
                Cue("pause", "", 600),
                Cue("emote", "idea", 800),
                Cue.text("Mitte."),
                Cue.text("Ende."),
            ),
            "idle",
            "talk",
            "story",
        )

    def test_click_skips_to_next_text_and_invalidates_old_callbacks(self) -> None:
        self.player.play(self.story)
        token = self.player.pending_timer
        assert token is not None
        stale = self.callbacks[token]
        self.assertTrue(self.player.advance_story())
        self.assertEqual(self.rendered, ["question", "Anfang."])
        self.assertTrue(self.player.advance_story())
        current = self.player.pending_timer
        self.assertEqual(self.rendered[-1], "Mitte.")
        assert callable(stale)
        stale()
        self.assertEqual(self.player.pending_timer, current)
        self.assertEqual(self.rendered[-1], "Mitte.")

    def test_last_click_completes_once_and_clears_the_surface(self) -> None:
        done = Mock()
        self.player.play(self.story, on_complete=done)
        for _ in range(4):
            self.assertTrue(self.player.advance_story())
        self.assertFalse(self.player.story_active)
        self.assertIsNone(self.player.pending_timer)
        self.assertEqual(self.callbacks, {})
        done.assert_called_once_with(True)
        self.assertFalse(self.player.advance_story())
        self.player.cancel()
        done.assert_called_once_with(True)
        self.hidden.assert_called()

    def test_explicit_replacement_cancels_without_completing_old_story(self) -> None:
        done = Mock()
        self.player.play(self.story, on_complete=done)
        self.player.play(Reaction.spoken("new", "Neue Aktion.", "idle", "pet"))
        done.assert_called_once_with(False)
        self.assertFalse(self.player.advance_story())
        self.assertEqual(self.rendered[-1], "Neue Aktion.")

    def test_pause_has_no_occupant_and_automatic_playback_completes(self) -> None:
        done = Mock()
        self.player.play(self.story, on_complete=done)
        for _ in self.story.beats:
            token = self.player.pending_timer
            assert token is not None
            callback = self.callbacks.pop(token)
            assert callable(callback)
            callback()
        done.assert_called_once_with(True)
        self.assertEqual(
            self.rendered, ["question", "Anfang.", "idea", "Mitte.", "Ende."]
        )

    def test_reading_contact_does_not_credit_care_or_escalate_clicks(self) -> None:
        state = PetState()
        before = vars(state).copy()
        mind = make_aiko_mind(started_at=0)
        adaptive = AdaptiveRoutine()
        contact = ContactCoordinator(
            state=state,
            mind=mind,
            adaptive=adaptive,
            ports=ContactPorts(
                context=lambda: context_at(0),
                toolbar_hidden=lambda: True,
                mark_hover=Mock(),
                interrupt_walk=Mock(),
                show_toolbar=Mock(),
                game_open=lambda: False,
                cancel_followup=Mock(),
                hide_speech=Mock(),
                react=Mock(),
                should_greet=lambda _now: False,
                story_active=lambda: self.player.story_active,
                advance_story=self.player.advance_story,
            ),
        )
        mind.clicks.extend([1, 2])
        self.player.play(self.story)
        with (
            patch.object(mind, "click") as click,
            patch.object(
                adaptive,
                "note_interaction",
            ) as note,
        ):
            for _ in range(4):
                contact.click("left")
        click.assert_not_called()
        note.assert_not_called()
        self.assertEqual(list(mind.clicks), [])
        self.assertEqual(vars(state), before)
        self.assertGreater(mind.last_contact, 0)
