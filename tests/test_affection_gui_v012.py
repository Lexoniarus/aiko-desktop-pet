"""GUI integration of the sixth value without touching v0.8 window stacking."""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.gui import DesktopPet
from aiko_pet.ui.action_toolbar import ActionToolbar
from aiko_pet.infrastructure.persistence import StateStore


class AffectionGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No display available") from error
        root.destroy()

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.app = DesktopPet(store=StateStore(Path(self.tempdir.name)/"pet.json"))
        self.addCleanup(self.app.quit)
        self.app.settings.auto_routine = False
        self.app.state.sleeping = False
        self.app._on_enter()
        self.app.root.update_idletasks()

    @property
    def toolbar(self) -> ActionToolbar:
        bar = self.app._hover.toolbar
        assert bar is not None
        return bar

    def test_six_hud_bars_stay_in_two_rows_and_fill_at_100_percent(self):
        toolbar = self.toolbar
        self.assertEqual(len(toolbar.NEEDS), 6)
        self.assertEqual(len(toolbar.needs), 6)
        for key in toolbar.needs:
            setattr(self.app.state, key, 100)
        toolbar.refresh()
        self.app.root.update_idletasks()
        toolbar.refresh()
        for key, (bar, rect, label) in toolbar.needs.items():
            self.assertEqual(bar.coords(rect)[2], bar.winfo_width(), key)
            self.assertIn("100%", label.cget("text"))
        self.assertIn("Zuwendung", toolbar.needs["affection"][2].cget("text"))
        self.assertIn("Lv 10", toolbar.needs["friendship"][2].cget("text"))

    def test_pet_button_refills_affection_without_refilling_energy(self):
        self.app.state.affection = 10
        self.app.state.social = 15
        self.app.state.energy = 44
        self.app.state.mood = 20
        self.toolbar.buttons["pet"].invoke()
        self.assertAlmostEqual(self.app.state.affection, 35, places=2)
        self.assertAlmostEqual(self.app.state.energy, 44, places=2)
        self.assertAlmostEqual(self.app.state.social, 17, places=2)
        self.assertAlmostEqual(self.app.state.mood, 26, places=2)
        self.toolbar.refresh()
        self.assertIn("35%", self.toolbar.needs["affection"][2].cget("text"))

    def test_separate_status_shows_affection_and_existing_controls(self):
        self.app._hover.open_status()
        panel = self.app._hover.status_panel
        assert panel is not None
        self.assertEqual(len(panel.bars), 6)
        self.app.state.affection = 46
        self.app.state.friendship = 93
        panel.refresh()
        self.assertIn("46%", panel.bars["affection"][2].cget("text"))
        self.assertIn("Lv 10", panel.bars["friendship"][2].cget("text"))
        self.assertIsNotNone(self.toolbar.settings_button)

    def test_existing_menu_drag_and_hide_remain_operational(self):
        self.toolbar.settings_button.invoke()
        self.assertIsNotNone(self.app._hover.settings_popup)
        self.app._hover.dismiss_outside(-999, -999)
        self.assertFalse(self.toolbar.visible)
        self.assertIsNone(self.app._hover.settings_popup)
        self.app._on_enter()
        self.assertTrue(self.toolbar.visible)


if __name__ == "__main__":
    unittest.main()
