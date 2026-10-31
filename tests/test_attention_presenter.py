"""The attention presenter only renders preselected effects."""

import unittest
from dataclasses import replace
from unittest.mock import Mock

from aiko_pet.ui.pet_view.attention_presenter import (
    AttentionPresenter,
    AttentionViewPorts,
)


class AttentionPresenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.react = Mock()
        self.animate = Mock()
        self.emote = Mock()
        self.text = Mock()
        self.presenter = AttentionPresenter(AttentionViewPorts(
            start_action=self.animate, react=self.react,
            show_emote=self.emote, show_text=self.text,
        ))

    def test_selected_reaction_is_forwarded_unchanged(self) -> None:
        reaction = Mock()
        self.presenter.show_reaction(reaction, 2600)
        self.react.assert_called_once_with(reaction, 2600)

    def test_idle_animation_and_emote_have_independent_outputs(self) -> None:
        self.presenter.show_animation("waiting", 1.6)
        self.presenter.show_idle_emote("sleeps")
        self.animate.assert_called_once_with("waiting", 1.6)
        self.emote.assert_called_once_with("sleeps", 1100)

    def test_notification_text_is_not_interpreted(self) -> None:
        self.presenter.show_notification("Kalender: Termin gleich.")
        self.text.assert_called_once_with("Kalender: Termin gleich.", 3500)

    def test_cursor_cue_only_uses_unlocked_emote_output(self):
        self.presenter.show_cursor_emote("question", 1500)
        self.emote.assert_called_once_with("question", 1500)
        self.react.assert_not_called()
        self.animate.assert_not_called()
        self.text.assert_not_called()

    def test_cursor_comment_uses_vacant_nonblocking_text_without_actions(self):
        display = Mock(return_value=True)
        self.presenter._ports = replace(self.presenter._ports,
                                        show_nonblocking_text=display)
        self.assertTrue(self.presenter.show_cursor_comment("Na warte!", 2200))
        display.assert_called_once_with("Na warte!", 2200)
        self.react.assert_not_called()
        self.animate.assert_not_called()
        self.emote.assert_not_called()
        self.text.assert_not_called()
