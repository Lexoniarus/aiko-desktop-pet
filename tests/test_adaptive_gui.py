"""Integration checks for adaptive settings and live Tk state."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.telemetry import ComputerSnapshot
from tools.desktop_test_support import create_test_desktop


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
        self.app = create_test_desktop(store=self.store)
        self.addCleanup(self.app.quit)
        self.app.settings.auto_routine = False

    def test_live_sample_updates_one_adaptive_situation(self):
        now = time.monotonic()
        snap = ComputerSnapshot(cpu=94, ram=40, measured_at=now)
        with patch.object(self.app.activity_monitor, "latest", return_value=snap), \
             patch("aiko_pet.gui.idle_seconds_windows", return_value=0):
            self.app._activity.observe_adaptive(now + 0.1, time.time())
            self.assertIsNotNone(self.app.adaptive.current)
            observed = self.app.adaptive.current
            assert observed is not None
            self.assertTrue(observed.focused)
            self.assertIs(self.app.mind.situation, self.app.adaptive.current)
            previous = self.app.adaptive.current
            self.app._activity.observe_adaptive(now + 5, time.time() + 5)
            self.assertIs(self.app.adaptive.current, previous)

    def test_learning_switch_does_not_disable_live_load_or_forget_data(self):
        self.app.settings.learn_rhythm = False
        now = time.monotonic()
        snap = ComputerSnapshot(gpu=98, ram=55, measured_at=now)
        with patch.object(self.app.activity_monitor, "latest", return_value=snap), \
             patch("aiko_pet.gui.idle_seconds_windows", return_value=220):
            self.app._activity.observe_adaptive(now + 0.2, time.time())
        observed = self.app.adaptive.current
        assert observed is not None
        self.assertTrue(observed.focused)
        self.assertEqual(sum(self.app.adaptive.memory.hour_seconds), 0)
        self.app.settings.learn_rhythm = True
        self.app.adaptive.memory.hour_seconds[9] = 40
        self.app.set_learn_rhythm(False)
        restored = self.store.load_session()
        self.assertEqual(restored.adaptive_memory.hour_seconds[9], 40)
        self.assertFalse(restored.settings.learn_rhythm)
        self.app.forget_rhythm()
        self.assertEqual(sum(self.store.load_session().adaptive_memory.hour_seconds), 0)

    def test_settings_window_exposes_learning_and_reset_controls(self):
        self.app._on_enter()
        bar = self.app._hover.toolbar
        assert bar is not None
        bar.settings_button.invoke()
        window = self.app._hover.settings_window
        assert window is not None
        self.assertIn("learn_rhythm", window.values)
        self.assertIn("Tagesmuster", window.forget_button.cget("text"))
        window.close()

    def test_status_details_show_activity_memory_without_extra_window(self):
        self.app.adaptive.memory.strain = 64
        now = time.monotonic()
        snap = ComputerSnapshot(cpu=92, ram=40, measured_at=now)
        with patch.object(self.app.activity_monitor, "latest", return_value=snap):
            self.app._activity.observe_adaptive(now + 0.1, time.time())
            self.app._hover.open_status()
            bar = self.app._hover.toolbar
            assert bar is not None and bar.details is not None
            bar.toggle_details()
            self.assertIn("Mein Rhythmus:", bar.details.text("activity_line"))
            self.assertIn("Beanspruchung", bar.details.text("activity_line"))

    def test_monitored_state_persists_without_changing_window_position(self):
        original = self.app.settings.x, self.app.settings.y
        self.app.adaptive.memory.strain = 43
        self.app._save()
        restored = self.store.load_session()
        self.assertEqual(restored.adaptive_memory.strain, 43)
        self.assertEqual((restored.settings.x, restored.settings.y), original)


if __name__ == "__main__":
    unittest.main()
