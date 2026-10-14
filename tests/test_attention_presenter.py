"""Attention presentation preserves suppression and UI action boundaries."""

import unittest
from unittest.mock import Mock

from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.attention_presenter import (
    AttentionPresenter,
    AttentionViewPorts,
)


class AttentionPresenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = Mock()
        self.policy.state = PetState()
        self.policy.mind = Mock()
        self.reactions: list[tuple[object, int]] = []
        self.icons: list[tuple[str, int]] = []
        self.ports = AttentionViewPorts(
            context=Mock(),
            game_open=lambda: False,
            toolbar_active=lambda: False,
            settings_engaged=lambda: False,
            bubble_visible=lambda: False,
            reaction_pending=lambda: False,
            walking=lambda: False,
            action_until=lambda: 0.0,
            start_action=Mock(),
            react=lambda reaction, ms: self.reactions.append((reaction, ms)),
            show_emote=lambda icon, ms: self.icons.append((icon, ms)),
            show_text=Mock(),
        )
        self.presenter = AttentionPresenter(self.policy, ports=self.ports)

    def test_cursor_speech_uses_existing_decision(self) -> None:
        reaction = Mock()
        self.policy.cursor_moved.return_value = "cursor_follow"
        self.policy.mind.say_event.return_value = reaction
        self.presenter.cursor_moved(150.0, 1920, 100.0)
        self.assertEqual(self.reactions, [(reaction, 2600)])
        self.policy.cursor_moved.assert_called_once_with(
            150.0, 1920, 100.0, toolbar_visible=False,
        )

    def test_idle_emote_uses_pet_state_without_new_need_values(self) -> None:
        self.policy.state.energy = 0
        self.presenter.idle_emote()
        self.assertEqual(self.icons, [("sleeps", 1100)])

    def test_no_notification_has_no_visual_effect(self) -> None:
        self.policy.next_notification.return_value = None
        self.presenter.present_notification(100.0)
        self.policy.mark_spoken.assert_not_called()
