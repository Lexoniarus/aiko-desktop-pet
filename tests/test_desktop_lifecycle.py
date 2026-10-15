"""Lifecycle startup and shutdown order without opening real Tk windows."""

from __future__ import annotations

import tkinter as tk
import unittest
from typing import cast
from unittest.mock import MagicMock

from aiko_pet.application.router import ApplicationRouter
from aiko_pet.desktop.input import DesktopInput
from aiko_pet.desktop.lifecycle import DesktopLifecycle
from aiko_pet.desktop.runtime import DesktopRuntime
from aiko_pet.desktop.window_stack import WindowStack
from aiko_pet.infrastructure.hardware.monitor import ActivityMonitor
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.pet_view.speech_presenter import SpeechPresenter
from aiko_pet.ui.windows.hover_ui import HoverUi


class DesktopLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calls: list[str] = []
        root = MagicMock(spec=tk.Tk)
        inputs = MagicMock(spec=DesktopInput)
        runtime = MagicMock(spec=DesktopRuntime)
        monitor = MagicMock(spec=ActivityMonitor)
        app = MagicMock(spec=ApplicationRouter)
        stack = MagicMock(spec=WindowStack)
        hover = MagicMock(spec=HoverUi)
        reaction = MagicMock(spec=ReactionPlayer)
        speech = MagicMock(spec=SpeechPresenter)
        for mock, name, label in (
            (inputs, "initialize", "input"),
            (root, "update_idletasks", "layout"),
            (root, "deiconify", "show"),
            (stack, "restore", "stack"),
            (monitor, "start", "monitor-start"),
            (runtime, "start", "runtime-start"),
            (app, "close", "app-close"),
            (runtime, "stop", "runtime-stop"),
            (inputs, "stop", "input-stop"),
            (monitor, "stop", "monitor-stop"),
            (reaction, "cancel", "cancel-reactions"),
            (speech, "hide", "hide-speech"),
            (hover, "close_game", "close-game"),
            (hover, "close_settings", "close-settings"),
            (hover, "close_toolbar", "close-toolbar"),
            (root, "destroy", "destroy"),
        ):
            getattr(mock, name).side_effect = (
                lambda value=label: self.calls.append(value)
            )
        self.hover = hover
        self.lifecycle = DesktopLifecycle(
            root=cast(tk.Tk, root), inputs=cast(DesktopInput, inputs),
            runtime=cast(DesktopRuntime, runtime),
            monitor=cast(ActivityMonitor, monitor),
            application=cast(ApplicationRouter, app),
            overlays=cast(WindowStack, stack), hover=cast(HoverUi, hover),
            reaction=cast(ReactionPlayer, reaction),
            speech=cast(SpeechPresenter, speech),
            place_initially=lambda: self.calls.append("place"),
            save=lambda: self.calls.append("save"),
            stop_animation=lambda: self.calls.append("animation-stop"),
        )

    def test_startup_maps_window_before_sampling_or_timers(self) -> None:
        self.lifecycle.start()
        self.lifecycle.start()
        self.assertEqual(self.calls, [
            "input", "place", "layout", "show", "stack",
            "monitor-start", "runtime-start",
        ])

    def test_prepare_farewell_keeps_root_alive_until_real_shutdown(self) -> None:
        self.lifecycle.prepare_farewell()
        self.assertEqual(self.calls, [
            "runtime-stop", "input-stop", "cancel-reactions",
            "close-game", "close-settings", "close-toolbar",
        ])
        self.assertNotIn("destroy", self.calls)
        self.assertNotIn("save", self.calls)
        self.lifecycle.stop()
        self.assertEqual(self.calls.count("save"), 1)
        self.assertEqual(self.calls.count("destroy"), 1)

    def test_shutdown_preserves_cleanup_order_and_is_idempotent(self) -> None:
        self.lifecycle.stop()
        self.lifecycle.stop()
        self.assertEqual(self.calls, [
            "runtime-stop", "input-stop", "close-game", "app-close",
            "animation-stop", "monitor-stop", "save",
            "cancel-reactions", "hide-speech",
            "close-settings", "close-toolbar", "destroy",
        ])

    def test_shutdown_prevents_late_startup(self) -> None:
        self.lifecycle.stop()
        self.calls.clear()
        self.lifecycle.start()
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
