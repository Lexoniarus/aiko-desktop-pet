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
        self.reactions: list[tuple[Reaction | None, int]] = []
        self.greet_enabled = True
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
                game_open=lambda: False,
                cancel_followup=self.cancel,
                hide_speech=self.hide,
                react=lambda reaction, duration: self.reactions.append(
                    (reaction, duration),
                ),
                should_greet=lambda _now: self.greet_enabled,
            ),
        )

    def test_hover_opens_toolbar_and_interrupts_walk(self) -> None:
        with patch.object(self.mind, "return_to_pet", return_value=None):
            self.contact.enter()
        self.hover.assert_called_once()
        self.interrupt.assert_called_once()
        self.show.assert_called_once()
        self.assertEqual(self.reactions, [(None, 2800)])

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
