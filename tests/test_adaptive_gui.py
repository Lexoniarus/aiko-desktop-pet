"""Integration checks for adaptive settings and live Tk state."""

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk

from aiko_pet.gui import DesktopPet
from aiko_pet.storage import StateStore
from aiko_pet.system_activity import ComputerSnapshot


class AdaptiveGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error)) from error
        root.withdraw()
        root.destroy()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = StateStore(Path(self.folder.name) / "state.json")
        self.app = DesktopPet(store=self.store)
        self.addCleanup(self.app.quit)
        self.app.settings.auto_routine = False

    def test_live_sample_updates_one_adaptive_situation(self):
        now = time.monotonic()
        snap = ComputerSnapshot(cpu=94, ram=40, measured_at=now)
        with patch.object(self.app.activity_monitor, "latest", return_value=snap), \
             patch("aiko_pet.gui.idle_seconds_windows", return_value=0):
            self.app._observe_adaptive(now + 0.1, time.time())
            self.assertIsNotNone(self.app.adaptive.current)
            self.assertTrue(self.app.adaptive.current.focused)
            self.assertIs(self.app.mind.situation, self.app.adaptive.current)
            previous = self.app.adaptive.current
            self.app._observe_adaptive(now + 5, time.time() + 5)
            self.assertIs(self.app.adaptive.current, previous)

    def test_learning_switch_does_not_disable_live_load_or_forget_data(self):
        self.app.settings.learn_rhythm = False
        now = time.monotonic()
        snap = ComputerSnapshot(gpu=98, ram=55, measured_at=now)
        with patch.object(self.app.activity_monitor, "latest", return_value=snap), \
             patch("aiko_pet.gui.idle_seconds_windows", return_value=220):
            self.app._observe_adaptive(now + 0.2, time.time())
        self.assertTrue(self.app.adaptive.current.focused)
        self.assertEqual(sum(self.app.adaptive.memory.hour_seconds), 0)
        self.app.settings.learn_rhythm = True
        self.app.adaptive.memory.hour_seconds[9] = 40
        self.app.set_learn_rhythm(False)
        self.assertEqual(self.store.load_memory().hour_seconds[9], 40)
        self.assertFalse(self.store.load()[1].learn_rhythm)
        self.app.forget_rhythm()
        self.assertEqual(sum(self.store.load_memory().hour_seconds), 0)

    def test_settings_popup_exposes_learning_and_reset_controls(self):
        self.app._on_enter()
        self.app.toolbar.settings_button.invoke()
        popup = self.app.settings_popup
        self.assertIn("learn_rhythm", popup.values)
        text = [child.cget("text") for child in
                popup.window.winfo_children()[0].winfo_children()
                if isinstance(child, tk.Button)]
        self.assertTrue(any("Tagesmuster" in label for label in text))
        popup.close()

    def test_status_shows_activity_memory_without_changing_overlay(self):
        self.app.adaptive.memory.strain = 64
        now = time.monotonic()
        snap = ComputerSnapshot(cpu=92, ram=40, measured_at=now)
        with patch.object(self.app.activity_monitor, "latest", return_value=snap):
            self.app._observe_adaptive(now + 0.1, time.time())
            self.app.open_status()
            panel = self.app.status_panel
            self.assertIn("Mein Rhythmus:", panel.life_label.cget("text"))
            self.assertIn("Beanspruchung", panel.life_label.cget("text"))
            panel.close()

    def test_monitored_state_persists_without_changing_window_position(self):
        original = self.app.settings.x, self.app.settings.y
        self.app.adaptive.memory.strain = 43
        self.app._save()
        restored = self.store.load_memory()
        self.assertEqual(restored.strain, 43)
        self.assertEqual((self.store.load()[1].x, self.store.load()[1].y), original)


if __name__ == "__main__":
    unittest.main()
