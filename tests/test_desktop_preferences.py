"""Headless desktop preference ownership and callback parity tests."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, patch

from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.application.activity import ActivityCoordinator
from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.settings import PetSettings, SettingKey
from aiko_pet.desktop.preferences import (
    DesktopPreferencePorts, DesktopPreferences,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import TimeContext
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet
from aiko_pet.ui.pet_view.desktop_window import DesktopWindow
from aiko_pet.ui.windows.hover_ui import HoverUi
from aiko_pet.ui.pet_view.speech_presenter import SpeechPresenter
from aiko_pet.desktop.window_stack import WindowStack


class DesktopPreferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = PetSettings(
            x=420, y=400, toolbar_x=35, toolbar_y=75,
        )
        self.state = PetState()
        self.adaptive = AdaptiveRoutine()
        self.activity = MagicMock(spec=ActivityCoordinator)
        self.attention = MagicMock(spec=AttentionCoordinator)
        self.animated = MagicMock(spec=AnimatedPet)
        self.animated.movement = MagicMock()
        self.animated.movement.remaining_distance = 140
        self.window = MagicMock(spec=DesktopWindow)
        self.window.width = 128
        self.window.track = SimpleNamespace(left=100, right=1000)
        self.window.placed = True
        self.hover = MagicMock(spec=HoverUi)
        self.hover.toolbar = None
        self.speech = MagicMock(spec=SpeechPresenter)
        self.stack = MagicMock(spec=WindowStack)
        self.stack.enabled = True
        self.saves = 0
        self.positions: list[float] = []
        self.contexts: list[TimeContext] = []

        def save() -> None:
            self.saves += 1

        self.prefs = DesktopPreferences(
            settings=self.settings,
            state=self.state,
            adaptive=self.adaptive,
            activity=cast(ActivityCoordinator, self.activity),
            attention=cast(AttentionCoordinator, self.attention),
            animated=cast(AnimatedPet, self.animated),
            window=cast(DesktopWindow, self.window),
            hover=cast(HoverUi, self.hover),
            speech=cast(SpeechPresenter, self.speech),
            overlay_stack=cast(WindowStack, self.stack),
            ports=DesktopPreferencePorts(
                place_x=self.positions.append,
                save=save,
                set_context=self.contexts.append,
            ),
        )

    def test_topmost_coordinates_existing_windows_then_saves(self) -> None:
        self.prefs.set_option("always_on_top", False)
        self.assertFalse(self.settings.always_on_top)
        self.assertFalse(self.stack.enabled)
        self.window.set_topmost.assert_called_once_with(False)
        self.hover.set_topmost.assert_called_once_with(False)
        self.speech.set_topmost.assert_called_once_with(False)
        self.stack.restore.assert_called_once()
        self.assertEqual(self.saves, 1)

    def test_routine_switch_advances_once_and_refreshes_status(self) -> None:
        with (
            patch.object(self.state, "advance") as advance,
            patch(
                "aiko_pet.desktop.preferences.time.time",
                return_value=1_781_000_000.0,
            ),
        ):
            self.prefs.set_option("auto_routine", False)
        advance.assert_not_called()
        self.activity.advance_state.assert_called_once_with(1_781_000_000.0)
        self.assertFalse(self.settings.auto_routine)
        self.assertEqual(len(self.contexts), 1)
        self.hover.refresh_status.assert_called_once()
        self.assertEqual(self.saves, 1)

    def test_scale_keeps_same_center_and_invalidates_sprite_gaze(self) -> None:
        self.prefs.toggle_scale()
        self.assertEqual(self.settings.scale, 2)
        self.window.resize.assert_called_once()
        self.animated.reload_sprites.assert_called_once()
        self.assertIsNone(self.animated.gaze_sector)
        self.assertFalse(self.window.placed)
        self.assertEqual(self.positions, [420.0])
        self.assertEqual(self.saves, 1)

    def test_feature_settings_have_single_owner_and_save(self) -> None:
        self.prefs.set_option("auto_walk", False)
        self.prefs.set_option("follow_cursor", False)
        self.prefs.set_option("spontaneous_talk", False)
        self.prefs.set_option("observe_computer", False)
        self.prefs.set_option("learn_rhythm", False)
        self.animated.set_auto_walk.assert_called_once()
        self.animated.set_follow_cursor.assert_called_once_with(False)
        self.attention.set_spontaneous_talk.assert_called_once()
        self.activity.set_observation_enabled.assert_called_once_with(False)
        self.assertFalse(self.settings.learn_rhythm)
        self.assertEqual(self.saves, 5)

    def test_unknown_option_does_not_change_or_save_anything(self) -> None:
        before = self.settings.to_dict()
        with self.assertRaises(ValueError):
            self.prefs.set_option(cast(SettingKey, "invalid"), True)
        self.assertEqual(self.settings.to_dict(), before)
        self.assertEqual(self.saves, 0)

    def test_drag_position_and_reset_without_toolbar_save_once(self) -> None:
        with patch("aiko_pet.desktop.preferences.time.monotonic",
                   return_value=120.0):
            self.prefs.record_toolbar_position(45, 72)
        self.assertEqual(
            (self.settings.toolbar_x, self.settings.toolbar_y), (45, 72),
        )
        self.assertEqual(self.hover.last_hover, 120.0)
        self.prefs.reset_toolbar_position()
        self.assertEqual(
            (self.settings.toolbar_x, self.settings.toolbar_y), (None, None),
        )
        self.assertEqual(self.saves, 2)

    def test_center_stops_walking_without_touching_hover(self) -> None:
        self.prefs.center()
        self.assertEqual(self.positions, [486.0])
        self.animated.movement.interrupt.assert_called_once_with()
        self.assertEqual(self.saves, 1)


if __name__ == "__main__":
    unittest.main()
