"""Tk desktop input is independent of care policy and HoverUi implementation."""

from __future__ import annotations

import tkinter as tk
import unittest
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.desktop.input import DesktopInput, DesktopInputActions


class FakeMouse:
    def __init__(self) -> None:
        self.pressed = False
        self.calls = 0

    def clicked(self) -> bool:
        self.calls += 1
        result = self.pressed
        self.pressed = False
        return result


class DesktopInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No Tk display") from error
        root.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()
        self.events: list[str] = []
        self.mouse = FakeMouse()
        self.closed = False
        self.input = DesktopInput(
            self.root, self.canvas, DesktopInputActions(
                enter=lambda _event: self.events.append("enter"),
                left_click=lambda _event: self.events.append("left"),
                right_click=lambda _event: self.events.append("right"),
                show_menu=lambda x, y: self.events.append(f"menu:{x}:{y}"),
                dismiss_outside=lambda x, y: self.events.append(
                    f"dismiss:{x}:{y}",
                ),
                open_status=lambda: self.events.append("status"),
                quit=lambda: self.events.append("quit"),
                closed=lambda: self.closed,
            ), self.mouse,
        )
        self.addCleanup(self.root.destroy)

    def test_pointer_sampling_uses_desktop_input_boundary(self) -> None:
        with (
            patch.object(self.root, "winfo_pointerx", return_value=321),
            patch.object(self.root, "winfo_pointery", return_value=654),
            patch.object(self.root, "winfo_screenwidth", return_value=1920),
        ):
            self.assertEqual(self.input.pointer_sample(), (321, 654, 1920))

    def test_entry_checks_origin_before_dispatch_but_keeps_clicks(self) -> None:
        self.input.actions = replace(self.input.actions, allow_hover=lambda: False)
        self.input.on_enter()
        self.assertEqual(self.events, [])
        self.input.actions.left_click(None)
        self.assertEqual(self.events, ["left"])
        self.input.actions = replace(self.input.actions, allow_hover=lambda: True)
        self.input.on_enter()
        self.assertEqual(self.events, ["left", "enter"])

    def test_native_click_claims_before_dispatch_without_hover(self):
        self.input.actions = replace(
            self.input.actions, allow_hover=lambda: False,
            claim_access=lambda _point: self.events.append("claim"),
        )
        self.input.on_left_click()
        self.input.on_right_click()
        self.assertEqual(self.events, ["claim", "left", "claim", "right"])

    def test_native_enter_opens_hover_without_claiming_input(self):
        self.input.actions = replace(
            self.input.actions, claim_access=lambda _point: self.events.append("claim"),
        )
        self.input.on_enter()
        self.assertEqual(self.events, ["enter"])

    def test_initial_bindings_preserve_sprite_events(self) -> None:
        self.input.initialize()
        self.assertEqual(self.mouse.calls, 1)
        self.assertIn("<Button-1>", self.canvas.bind())
        self.assertIn("<Button-3>", self.canvas.bind())
        self.assertIn("<Shift-Button-3>", self.canvas.bind())

    def test_tk_click_and_menu_use_explicit_action_ports(self) -> None:
        event = tk.Event()
        event.x_root, event.y_root = 25, 39
        self.input.on_tk_press(event)
        self.input.on_menu(event)
        self.assertEqual(self.events, ["dismiss:25:39", "menu:25:39"])

    def test_focus_timers_are_cancelled_before_root_teardown(self) -> None:
        self.input.initialize()
        self.input.on_focus_out(tk.Event())
        self.input.on_focus_out(tk.Event())
        self.assertEqual(len(self.input._focus_timers), 2)
        pending = tuple(self.input._focus_timers)
        for timer in pending:
            self.assertIn(timer, self.root.tk.call("after", "info"))
        self.input.stop()
        self.input.stop()
        self.assertEqual(self.input._focus_timers, set())
        for timer in pending:
            self.assertNotIn(timer, self.root.tk.call("after", "info"))
        self.input.on_focus_out(tk.Event())
        self.assertEqual(self.input._focus_timers, set())

    def test_stop_detaches_sprite_input_during_farewell(self) -> None:
        self.input.initialize()
        self.input.stop()
        self.assertFalse(self.canvas.bind("<Enter>"))
        self.assertFalse(self.canvas.bind("<Button-1>"))
        self.assertFalse(self.canvas.bind("<Button-3>"))
        self.assertFalse(self.canvas.bind("<Shift-Button-3>"))
        event = tk.Event()
        event.x_root, event.y_root = 25, 39
        self.input.on_menu(event)
        self.input.on_tk_press(event)
        self.assertEqual(self.events, [])

    def test_global_click_and_closed_focus_are_separate(self) -> None:
        self.input.poll_global_click()
        self.assertEqual(self.events, [])
        self.closed = True
        self.input.dismiss_after_focus_loss()
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
