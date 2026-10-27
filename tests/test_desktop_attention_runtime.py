"""Application attention decisions are resolved outside the UI presenter."""

import unittest
from dataclasses import replace
from unittest.mock import Mock

from aiko_pet.application.activity import TimeProgress
from aiko_pet.application.attention import AttentionCoordinator, SpontaneousChoice
from aiko_pet.application.events import IncomingNotification
from aiko_pet.desktop.attention_runtime import (
    AttentionRuntimePorts,
    DesktopAttentionRuntime,
)
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.interaction_events import CursorExperience, CursorWarning
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.attention_presenter import AttentionPresenter
from tools.pet_test_support import set_test_pet_values


class DesktopAttentionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.attention = Mock(spec=AttentionCoordinator)
        self.attention.state = PetState()
        self.attention.mind = Mock()
        self.attention.mind.emotional_state.return_value = EmotionalComposition(
            EmotionalState.SATISFIED
        )
        self.presenter = Mock(spec=AttentionPresenter)
        self.context = context_at(1_781_000_000.0)
        self.toolbar_refresh = Mock()
        self.runtime = DesktopAttentionRuntime(
            self.attention,
            self.presenter,
            AttentionRuntimePorts(
                context=lambda: self.context,
                game_open=lambda: False,
                menu_engaged=lambda: False,
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
            123.0,
            self.context,
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
        self.attention.evaluate_wishes.assert_called_once_with()

    def test_period_change_without_sleep_refreshes_only_toolbar(self) -> None:
        self.runtime.handle_time_progress(
            TimeProgress(self.context, period_changed=True, sleep_changed=False),
            123.0,
        )
        self.toolbar_refresh.assert_called_once_with()
        self.attention.select_sleep_transition_reaction.assert_not_called()

    def test_warning_uses_catalogue_and_reports_only_actual_display(self):
        from aiko_pet.pet.mind.catalog import Reaction

        reaction = Reaction.spoken(
            "warning", "Hey, langsamer!", "idle", "cursor_warning_near_fast",
        )
        self.attention.mind.select_reaction.return_value = reaction
        self.presenter.show_cursor_warning.return_value = True
        before = self.attention.state.capture_checkpoint()
        receipt = self.runtime.cursor_warning(CursorWarning("fresh", 10), 10)
        self.assertTrue(receipt.presented)
        self.assertEqual(receipt.warning_id, "fresh")
        self.attention.mind.select_reaction.assert_called_once_with(
            "cursor_warning_near_fast", self.attention.state, self.context, 10,
        )
        self.presenter.show_reaction.assert_not_called()
        self.assertEqual(before, self.attention.state.capture_checkpoint())
        self.presenter.show_cursor_warning.return_value = False
        receipt = self.runtime.cursor_warning(CursorWarning("next", 11), 11)
        self.assertFalse(receipt.presented)

    def test_warning_drops_in_protected_or_occupied_slot_and_when_stale(self):
        original = self.runtime._ports
        for guard in ("game_open", "foreground_active", "reaction_pending",
                      "bubble_visible", "menu_engaged", "settings_engaged"):
            self.runtime._ports = replace(original, **{guard: lambda: True})
            self.assertFalse(
                self.runtime.cursor_warning(CursorWarning(guard, 10), 10).presented
            )
        self.runtime._ports = original
        receipt = self.runtime.cursor_warning(CursorWarning("old", 10), 11)
        self.assertFalse(receipt.presented)
        self.presenter.show_cursor_warning.assert_not_called()

    def test_qualified_cursor_cue_does_not_start_action_or_reaction(self):
        self.runtime.cursor_experience(CursorExperience("actual:1", "curiosity", 2))
        self.presenter.show_cursor_emote.assert_called_once_with("idea", 1500)
        self.presenter.show_reaction.assert_not_called()
        self.presenter.show_animation.assert_not_called()
        self.attention.cursor_reaction.assert_not_called()

    def test_occupied_slots_drop_cue_without_replay(self):
        original = self.runtime._ports
        for guard in ("game_open", "foreground_active", "reaction_pending",
                      "bubble_visible", "menu_engaged", "settings_engaged"):
            with self.subTest(guard=guard):
                self.runtime._ports = replace(original, **{guard: lambda: True})
                self.runtime.cursor_experience(CursorExperience(guard, "fear", 3))
                self.presenter.show_cursor_emote.assert_not_called()
        self.runtime._ports = original
        self.assertFalse(self.presenter.mock_calls)

    def test_notification_is_not_duplicated_or_changed(self) -> None:
        note = IncomingNotification(
            event_id="test",
            source="test.browser",
            title="Kalender",
            message="Termin gleich.",
        )
        self.attention.next_notification.return_value = note
        self.runtime.present_notification(100.0)
        self.presenter.show_notification.assert_called_once_with(
            "Kalender: Termin gleich.",
            3500,
        )
        self.attention.mark_spoken.assert_called_once_with(100.0)

    def test_idle_emote_comes_from_pet_needs(self) -> None:
        set_test_pet_values(self.attention.state, energy=0)
        self.runtime.idle_emote()
        self.presenter.show_idle_emote.assert_called_once_with("sleeps")

    def test_spontaneous_decision_uses_existing_timing(self) -> None:
        reaction = Mock()
        self.attention.spontaneous.return_value = SpontaneousChoice(True, reaction)
        self.runtime.maybe_speak_spontaneously(100.0)
        self.presenter.show_reaction.assert_called_once_with(reaction, 3600)
