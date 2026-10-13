"""Desktop Tk window geometry without a full pet or any hover widgets."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.application.settings import PetSettings
from aiko_pet.ui.desktop_window import DesktopWindow


class DesktopWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No Tk display") from error
        probe.destroy()

    def setUp(self) -> None:
        self.settings = PetSettings()
        self.window = DesktopWindow(self.settings)
        self.addCleanup(self.window.root.destroy)

    def test_saved_position_and_taskbar_grounding(self) -> None:
        self.assertFalse(self.window.placed)
        initial = self.window.initial_x()
        self.assertTrue(self.window.place_x(initial))
        self.assertTrue(self.window.placed)
        self.assertFalse(self.window.place_x(initial))
        self.assertEqual(
            self.settings.y,
            self.window.track.sprite_y(self.settings.scale),
        )

    def test_scale_resize_requires_reposition(self) -> None:
        self.window.place_x(self.window.initial_x())
        self.settings.scale = 2
        self.window.resize()
        self.assertFalse(self.window.placed)
        self.assertEqual((self.window.width, self.window.height), (384, 416))
        self.assertTrue(self.window.place_x(self.settings.x or 0))
        self.assertEqual(self.settings.y, self.window.track.sprite_y(2))


if __name__ == "__main__":
    unittest.main()
