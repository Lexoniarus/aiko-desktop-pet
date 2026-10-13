"""Tk desktop input is independent of care policy and HoverUi implementation."""

from __future__ import annotations

import tkinter as tk
import unittest

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

    def test_global_click_and_closed_focus_are_separate(self) -> None:
        self.input.poll_global_click()
        self.assertEqual(self.events, [])
        self.closed = True
        self.input.dismiss_after_focus_loss()
        self.assertEqual(self.events, [])


if __name__ == "__main__":
    unittest.main()
