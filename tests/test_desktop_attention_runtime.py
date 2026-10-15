"""Application attention decisions are resolved outside the UI presenter."""

import unittest
from unittest.mock import Mock

from aiko_pet.application.attention import AttentionCoordinator, SpontaneousChoice
from aiko_pet.application.activity import TimeProgress
from aiko_pet.application.events import IncomingNotification
from aiko_pet.desktop.attention_runtime import (
    AttentionRuntimePorts, DesktopAttentionRuntime,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at
from aiko_pet.ui.pet_view.attention_presenter import AttentionPresenter


class DesktopAttentionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.attention = Mock(spec=AttentionCoordinator)
        self.attention.state = PetState()
        self.presenter = Mock(spec=AttentionPresenter)
        self.context = context_at(1_781_000_000.0)
        self.toolbar_refresh = Mock()
        self.runtime = DesktopAttentionRuntime(
            self.attention, self.presenter,
            AttentionRuntimePorts(
                context=lambda: self.context,
                game_open=lambda: False,
                toolbar_active=lambda: False,
                settings_engaged=lambda: False,
                bubble_visible=lambda: False,
                reaction_pending=lambda: False,
                walking=lambda: False,
                action_until=lambda: 0.0,
                refresh_toolbar=self.toolbar_refresh,
            ),
        )

    def test_period_transition_refreshes_and_presents_sleep_dialogue(self) -> None:
        reaction = Mock()
        self.attention.select_sleep_transition_reaction.return_value = reaction
        self.runtime.handle_time_progress(
            TimeProgress(self.context, period_changed=True, sleep_changed=True),
            123.0,
        )
        self.toolbar_refresh.assert_called_once_with()
        self.attention.select_sleep_transition_reaction.assert_called_once_with(
            123.0, self.context,
        )
        self.presenter.show_reaction.assert_called_once_with(reaction, 2600)

    def test_no_period_transition_does_not_touch_presentation(self) -> None:
        self.runtime.handle_time_progress(
            TimeProgress(self.context, period_changed=False, sleep_changed=True),
            123.0,
        )
        self.toolbar_refresh.assert_not_called()
        self.attention.select_sleep_transition_reaction.assert_not_called()
        self.presenter.show_reaction.assert_not_called()

    def test_period_change_without_sleep_refreshes_only_toolbar(self) -> None:
        self.runtime.handle_time_progress(
            TimeProgress(self.context, period_changed=True, sleep_changed=False),
            123.0,
        )
        self.toolbar_refresh.assert_called_once_with()
        self.attention.select_sleep_transition_reaction.assert_not_called()

    def test_cursor_comment_is_selected_before_rendering(self) -> None:
        reaction = Mock()
        self.attention.cursor_reaction.return_value = reaction
        self.runtime.cursor_moved(120.0, 1920, 100.0)
        self.attention.cursor_reaction.assert_called_once_with(
            120.0, 1920, 100.0, self.context, toolbar_visible=False,
        )
        self.presenter.show_reaction.assert_called_once_with(reaction, 2600)

    def test_walk_comment_does_not_render_when_suppressed(self) -> None:
        self.attention.walk_reaction.return_value = None
        self.runtime.walk_finished(100.0)
        self.presenter.show_reaction.assert_not_called()

    def test_notification_is_not_duplicated_or_changed(self) -> None:
        note = IncomingNotification(
            event_id="test", source="test.browser",
            title="Kalender", message="Termin gleich.",
        )
        self.attention.next_notification.return_value = note
        self.runtime.present_notification(100.0)
        self.presenter.show_notification.assert_called_once_with(
            "Kalender: Termin gleich.", 3500,
        )
        self.attention.mark_spoken.assert_called_once_with(100.0)

    def test_idle_emote_comes_from_pet_needs(self) -> None:
        self.attention.state.energy = 0
        self.runtime.idle_emote()
        self.presenter.show_idle_emote.assert_called_once_with("sleeps")

    def test_spontaneous_decision_uses_existing_timing(self) -> None:
        reaction = Mock()
        self.attention.spontaneous.return_value = SpontaneousChoice(True, reaction)
        self.runtime.maybe_speak_spontaneously(100.0)
        self.presenter.show_reaction.assert_called_once_with(reaction, 3600)
