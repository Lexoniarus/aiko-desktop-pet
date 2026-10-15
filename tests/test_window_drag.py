"""Shared drag geometry and local Tk bindings, independent of pet state."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.ui.common.window_drag import WindowDrag, bounded_position


class WindowPositionTests(unittest.TestCase):
    def test_display_edges(self) -> None:
        self.assertEqual(bounded_position(-50, -60, 100, 80, 800, 600), (0, 0))
        self.assertEqual(bounded_position(900, 700, 100, 80, 800, 600), (700, 520))
        self.assertEqual(bounded_position(10, 20, 100, 80, 800, 600), (10, 20))

    def test_oversized_window_keeps_its_title_reachable(self) -> None:
        self.assertEqual(bounded_position(20, 30, 900, 700, 800, 600), (0, 0))


class WindowDragTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No Tk display") from error
        self.addCleanup(self.root.destroy)
        self.root.withdraw()
        self.window = tk.Toplevel(self.root)
        self.window.overrideredirect(True)
        self.window.geometry("200x100+30+40")
        self.header = tk.Label(self.window, text="Drag here")
        self.header.pack()
        self.button = tk.Button(self.window, text="Not a drag handle")
        self.button.pack()
        self.positions: list[tuple[int, int]] = []
        self.drag = WindowDrag(
            self.window, self.header,
            dropped=lambda x, y: self.positions.append((x, y)),
        )
        self.root.update_idletasks()
        self.addCleanup(self.drag.close)

    def test_only_title_is_bound_and_dragging_is_cleared(self) -> None:
        self.assertTrue(self.header.bind("<B1-Motion>"))
        self.assertFalse(self.button.bind("<B1-Motion>"))
        event = tk.Event()
        event.x_root, event.y_root = 50, 50
        self.drag.start(event)
        self.assertTrue(self.drag.dragging)
        event.x_root, event.y_root = 150, 100
        self.drag.move(event)
        self.drag.finish(event)
        self.assertFalse(self.drag.dragging)
        self.assertEqual(self.positions, [(130, 90)])
        self.drag.finish(event)
        self.assertEqual(len(self.positions), 1)

    def test_close_removes_owned_bindings(self) -> None:
        self.drag.close()
        self.drag.close()
        event = tk.Event()
        event.x_root, event.y_root = 50, 50
        self.drag.start(event)
        self.drag.move(event)
        self.drag.finish(event)
        self.assertFalse(self.drag.dragging)
        self.assertEqual(self.positions, [])
        self.assertFalse(self.header.bind("<B1-Motion>"))


if __name__ == "__main__":
    unittest.main()
