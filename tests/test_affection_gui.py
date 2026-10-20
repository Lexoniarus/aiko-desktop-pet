"""GUI integration of affection, care controls and persistent windows."""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from tools.desktop_test_support import create_test_desktop
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
        self.app = create_test_desktop(
            store=StateStore(Path(self.tempdir.name) / "pet.json"),
        )
        self.addCleanup(self.app.quit)
        self.app.settings.auto_routine = False
        set_test_pet_values(self.app.state, sleeping=False)
        self.app._hover.show_toolbar()
        self.app.root.update_idletasks()

    @property
    def toolbar(self) -> ActionToolbar:
        bar = self.app._hover.toolbar
        assert bar is not None
        return bar

    def test_mood_above_six_need_bars_and_fill_at_100_percent(self):
        toolbar = self.toolbar
        self.assertEqual(len(toolbar.READOUTS), 7)
        self.assertEqual(len(toolbar.readouts), 7)
        mood = toolbar.readouts["mood"].canvas
        previous = mood.winfo_rooty()
        for key in ("satiety", "fun", "energy", "social", "affection", "friendship"):
            readout = toolbar.readouts[key]
            self.assertGreater(readout.canvas.winfo_rooty(), previous)
            previous = readout.canvas.winfo_rooty()
        for key in toolbar.readouts:
            set_test_pet_values(self.app.state, **{key: 100})
        toolbar.refresh()
        self.app.root.update()
        toolbar.refresh()
        self.assertLess(
            mood.winfo_width(), toolbar.readouts["fun"].canvas.winfo_width()
        )
        for key, readout in toolbar.readouts.items():
            bar, rect, label = readout.canvas, readout._fill, readout.label
            self.assertEqual(max(bar.coords(rect)[::2]), bar.winfo_width() - 2, key)
            self.assertIn("100 / 100", label.cget("text"))
        self.assertIn("Zuwendung", toolbar.readouts["affection"].label.cget("text"))
        self.assertIn("Spaß", toolbar.readouts["fun"].label.cget("text"))
        self.assertIn("Lv 10", toolbar.readouts["friendship"].label.cget("text"))

    def test_pet_button_refills_affection_without_refilling_energy(self):
        set_test_pet_values(self.app.state, affection=10)
        set_test_pet_values(self.app.state, social=15)
        set_test_pet_values(self.app.state, energy=44)
        set_test_pet_values(self.app.state, mood=20)
        # Isolate the button effect from real time spent creating native windows.
        with patch.object(self.app._activity._clock, "consume", return_value=0):
            self.toolbar.buttons["pet"].invoke()
        self.assertAlmostEqual(self.app.state.affection, 35, places=2)
        self.assertAlmostEqual(self.app.state.energy, 44, places=2)
        self.assertAlmostEqual(self.app.state.social, 17, places=2)
        self.assertEqual(self.app.state.mood, 20)
        self.toolbar.refresh()
        self.assertIn("35 / 100", self.toolbar.readouts["affection"].label.cget("text"))

    def test_pinned_status_shows_affection_and_existing_controls(self):
        before = self.toolbar
        self.app._hover.open_status()
        self.assertIs(self.toolbar, before)
        self.assertTrue(self.app._hover.keep_open)
        self.assertEqual(len(self.toolbar.readouts), 7)
        set_test_pet_values(self.app.state, affection=46)
        set_test_pet_values(self.app.state, friendship=93)
        self.toolbar.refresh()
        self.assertIn("46 / 100", self.toolbar.readouts["affection"].label.cget("text"))
        self.assertIn("Lv 10", self.toolbar.readouts["friendship"].label.cget("text"))
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
