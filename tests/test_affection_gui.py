"""GUI integration of affection, care controls and persistent windows."""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from tools.pet_test_support import set_test_pet_values


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
        self.app = DesktopPet(store=StateStore(Path(self.tempdir.name) / "pet.json"))
        self.addCleanup(self.app.quit)
        self.app.settings.auto_routine = False
        set_test_pet_values(self.app.state, sleeping=False)
        self.app._on_enter()
        self.app.root.update_idletasks()

    @property
    def toolbar(self) -> ActionToolbar:
        bar = self.app._hover.toolbar
        assert bar is not None
        return bar

    def test_mood_above_six_need_bars_and_fill_at_100_percent(self):
        toolbar = self.toolbar
        self.assertEqual(len(toolbar.NEEDS), 7)
        self.assertEqual(len(toolbar.needs), 7)
        mood = toolbar.needs["mood"][0]
        assert isinstance(mood.master, tk.Frame)
        self.assertEqual(int(mood.master.grid_info()["columnspan"]), 3)
        for key in ("satiety", "fun", "energy", "social", "affection", "friendship"):
            bar = toolbar.needs[key][0]
            assert isinstance(bar.master, tk.Frame)
            self.assertGreater(int(bar.master.grid_info()["row"]), 0)
        fun_cell = toolbar.needs["fun"][0].master
        assert isinstance(fun_cell, tk.Frame)
        self.assertEqual(int(fun_cell.grid_info()["column"]), 1)
        for key in toolbar.needs:
            set_test_pet_values(self.app.state, **{key: 100})
        toolbar.refresh()
        self.app.root.update()
        toolbar.refresh()
        self.assertGreater(mood.winfo_width(), toolbar.needs["fun"][0].winfo_width())
        for key, (bar, rect, label) in toolbar.needs.items():
            self.assertEqual(bar.coords(rect)[2], bar.winfo_width(), key)
            self.assertIn("100%", label.cget("text"))
        self.assertIn("Zuwendung", toolbar.needs["affection"][2].cget("text"))
        self.assertIn("Spaß", toolbar.needs["fun"][2].cget("text"))
        self.assertIn("Lv 10", toolbar.needs["friendship"][2].cget("text"))

    def test_pet_button_refills_affection_without_refilling_energy(self):
        set_test_pet_values(self.app.state, affection=10)
        set_test_pet_values(self.app.state, social=15)
        set_test_pet_values(self.app.state, energy=44)
        set_test_pet_values(self.app.state, mood=20)
        self.toolbar.buttons["pet"].invoke()
        self.assertAlmostEqual(self.app.state.affection, 35, places=2)
        self.assertAlmostEqual(self.app.state.energy, 44, places=2)
        self.assertAlmostEqual(self.app.state.social, 17, places=2)
        self.assertGreater(self.app.state.mood, 20)
        self.toolbar.refresh()
        self.assertIn("35%", self.toolbar.needs["affection"][2].cget("text"))

    def test_pinned_status_shows_affection_and_existing_controls(self):
        before = self.toolbar
        self.app._hover.open_status()
        self.assertIs(self.toolbar, before)
        self.assertTrue(self.app._hover.keep_open)
        self.assertEqual(len(self.toolbar.needs), 7)
        set_test_pet_values(self.app.state, affection=46)
        set_test_pet_values(self.app.state, friendship=93)
        self.toolbar.refresh()
        self.assertIn("46%", self.toolbar.needs["affection"][2].cget("text"))
        self.assertIn("Lv 10", self.toolbar.needs["friendship"][2].cget("text"))
        self.assertIsNotNone(self.toolbar.settings_button)

    def test_settings_survive_toolbar_hide_and_reopen(self):
        self.toolbar.settings_button.invoke()
        settings = self.app._hover.settings_window
        self.assertIsNotNone(settings)
        self.app._hover.dismiss_outside(-999, -999)
        self.assertFalse(self.toolbar.visible)
        self.assertIs(self.app._hover.settings_window, settings)
        self.app._on_enter()
        self.assertTrue(self.toolbar.visible)


if __name__ == "__main__":
    unittest.main()
