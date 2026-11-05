"""Headless cancellation tests for focus callbacks across desktop shutdown."""

from __future__ import annotations

import tkinter as tk
import unittest
from typing import Callable, cast
from unittest.mock import MagicMock

from aiko_pet.desktop.input import DesktopInput, DesktopInputActions


class FakeMouse:
    def __init__(self) -> None:
        self.calls = 0

    def clicked(self) -> bool:
        self.calls += 1
        return False


class DesktopFocusTimerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = MagicMock(spec=tk.Tk)
        self.canvas = MagicMock(spec=tk.Canvas)
        self.callbacks: dict[str, Callable[[], None]] = {}
        self.cancelled: list[str] = []
        self.dismissed: list[tuple[int, int]] = []
        self.passively_dismissed: list[tuple[int, int]] = []
        self.closed = False
        self.mouse = FakeMouse()

        def schedule(_milliseconds: int, callback: Callable[[], None]) -> str:
            key = f"focus-{len(self.callbacks) + 1}"
            self.callbacks[key] = callback
            return key

        self.root.after.side_effect = schedule
        self.root.after_cancel.side_effect = self.cancelled.append
        self.root.winfo_pointerx.return_value = 5
        self.root.winfo_pointery.return_value = 7
        self.inputs = DesktopInput(
            cast(tk.Tk, self.root),
            cast(tk.Canvas, self.canvas),
            DesktopInputActions(
                enter=lambda _: None,
                left_click=lambda _: None,
                right_click=lambda _: None,
                show_menu=lambda _x, _y: None,
                dismiss_outside=lambda x, y: self.dismissed.append((x, y)),
                dismiss_passively=lambda x, y: self.passively_dismissed.append((x, y)),
                open_status=lambda: None,
                quit=lambda: None,
                closed=lambda: self.closed,
            ),
            mouse=self.mouse,
        )

    def test_stop_cancels_every_pending_focus_timer_once(self) -> None:
        self.inputs.on_focus_out(tk.Event())
        self.inputs.on_focus_out(tk.Event())
        self.assertEqual(len(self.inputs._focus_timers), 2)
        self.inputs.stop()
        self.inputs.stop()
        self.assertEqual(set(self.cancelled), {"focus-1", "focus-2"})
        self.assertEqual(len(self.cancelled), 2)
        self.assertEqual(self.inputs._focus_timers, set())
        self.assertEqual(self.dismissed, [])
        self.inputs.on_focus_out(tk.Event())
        self.assertEqual(len(self.callbacks), 2)

    def test_finished_focus_timer_is_not_cancelled_again(self) -> None:
        self.inputs.on_focus_out(tk.Event())
        self.callbacks["focus-1"]()
        self.assertEqual(self.dismissed, [])
        self.assertEqual(self.passively_dismissed, [(5, 7)])
        self.inputs.stop()
        self.assertEqual(self.cancelled, [])

    def test_stale_callback_cannot_operate_after_stop(self) -> None:
        self.inputs.on_focus_out(tk.Event())
        callback = self.callbacks["focus-1"]
        self.inputs.stop()
        callback()
        self.inputs.dismiss_after_focus_loss()
        self.inputs.poll_global_click()
        self.assertEqual(self.dismissed, [])
        self.assertEqual(self.mouse.calls, 0)
        self.assertEqual(self.passively_dismissed, [])

    def test_closed_desktop_does_not_schedule_focus_checks(self) -> None:
        self.closed = True
        self.inputs.on_focus_out(tk.Event())
        self.assertEqual(self.callbacks, {})


if __name__ == "__main__":
    unittest.main()
