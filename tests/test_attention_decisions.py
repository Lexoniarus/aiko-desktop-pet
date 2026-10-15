"""The application resolves attention dialogue before presentation."""

import unittest
from unittest.mock import Mock, patch

from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.settings import PetSettings
from aiko_pet.pet.mind import PetMind
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at


class AttentionDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mind = PetMind()
        self.state = PetState()
        self.context = context_at(1_781_000_000.0)
        self.attention = AttentionCoordinator(
            self.state, PetSettings(), self.mind, Mock(), Mock(), Mock(),
            started_at=0.0,
        )

    def test_cursor_reaction_uses_one_preselected_event(self) -> None:
        reaction = Mock()
        with (
            patch.object(self.attention, "select_cursor_comment_event",
                         return_value="cursor_follow") as detect,
            patch.object(self.mind, "say_event", return_value=reaction) as say,
        ):
            actual = self.attention.cursor_reaction(
                200.0, 1920, 100.0, self.context, toolbar_visible=False,
            )
        self.assertIs(actual, reaction)
        detect.assert_called_once_with(
            200.0, 1920, 100.0, toolbar_visible=False,
        )
        say.assert_called_once_with(
            "cursor_follow", self.state, self.context, 100.0,
        )

    def test_suppression_does_not_invoke_dialogue_book(self) -> None:
        with (
            patch.object(self.attention, "select_cursor_comment_event", return_value=None),
            patch.object(self.mind, "say_event") as say,
        ):
            actual = self.attention.cursor_reaction(
                200.0, 1920, 100.0, self.context, toolbar_visible=True,
            )
        self.assertIsNone(actual)
        say.assert_not_called()

    def test_sleep_transition_uses_current_state_and_dialogue(self) -> None:
        reaction = Mock()
        with patch.object(self.mind, "say_event", return_value=reaction) as say:
            self.state.sleeping = True
            self.assertIs(
                self.attention.select_sleep_transition_reaction(
                    100.0, self.context,
                ),
                reaction,
            )
            say.assert_called_once_with(
                "sleep", self.state, self.context, 100.0,
            )

        self.state.sleeping = False
        with patch.object(self.mind, "say_event", return_value=reaction) as say:
            self.attention.select_sleep_transition_reaction(101.0, self.context)
            say.assert_called_once_with(
                "wake", self.state, self.context, 101.0,
            )

    def test_disabled_spontaneous_talk_suppresses_sleep_transition(self) -> None:
        self.attention.settings.spontaneous_talk = False
        with patch.object(self.mind, "say_event") as say:
            self.assertIsNone(
                self.attention.select_sleep_transition_reaction(
                    100.0, self.context,
                ),
            )
            say.assert_not_called()

    def test_walk_pause_reaction_keeps_existing_gate(self) -> None:
        reaction = Mock()
        with (
            patch.object(self.attention, "should_comment_after_walk", return_value=True),
            patch.object(self.mind, "say_event", return_value=reaction) as say,
        ):
            actual = self.attention.walk_reaction(100.0, self.context)
        self.assertIs(actual, reaction)
        say.assert_called_once_with(
            "walk_pause", self.state, self.context, 100.0,
        )
