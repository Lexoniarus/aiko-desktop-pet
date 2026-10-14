"""GUI wiring for five stats, drink and relationship actions."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.gui import DesktopPet
from aiko_pet.ui.action_toolbar import ActionToolbar
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.telemetry import ComputerSnapshot


class CareGuiV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No display available") from error
        root.destroy()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.app = DesktopPet(store=StateStore(Path(self.folder.name) / "save.json"))
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

    def test_hover_has_five_needs_and_five_100_percent_bars(self):
        self.assertEqual(set(self.toolbar.needs), {
            "satiety", "mood", "energy", "social", "affection", "friendship",
        })
        for key in self.toolbar.needs:
            setattr(self.app.state, key, 100)
        self.toolbar.refresh()
        self.app.root.update()
        for key, (canvas, rect, label) in self.toolbar.needs.items():
            self.assertEqual(canvas.coords(rect)[2], canvas.winfo_width())
            self.assertIn("100%", label.cget("text"))
        self.assertIn("Lv 10", self.toolbar.needs["friendship"][2].cget("text"))

    def test_social_and_energy_actions_work_without_pinning(self):
        self.assertFalse(self.app._hover.keep_open)
        self.app.state.social = 9
        self.app.state.energy = 12
        self.toolbar.buttons["talk"].invoke()
        self.assertAlmostEqual(self.app.state.social, 35, places=2)
        self.toolbar.buttons["feed"].invoke()
        menu = self.app._hover.food_menu
        assert menu is not None
        menu.buttons["energy_drink"].invoke()
        self.assertAlmostEqual(self.app.state.energy, 21, places=2)
        self.assertNotIn("energy_drink", self.toolbar.buttons)
        self.assertFalse(self.app._hover.keep_open)
        self.toolbar.refresh()
        self.assertIn("35%", self.toolbar.needs["social"][2].cget("text"))

    def test_relationship_and_needs_in_pinned_toolbar(self):
        self.app._hover.open_status()
        self.assertTrue(self.app._hover.keep_open)
        self.assertEqual(set(self.toolbar.needs), {
            "satiety", "mood", "energy", "social", "affection", "friendship",
        })
        self.app.state.friendship = 85
        self.toolbar.refresh()
        self.assertIn("Lv 9", self.toolbar.needs["friendship"][2].cget("text"))

    def test_lagged_or_disabled_hardware_has_no_live_effort(self):
        snapshot = ComputerSnapshot(cpu=97, gpu=88, measured_at=time.monotonic())
        with patch.object(self.app.activity_monitor, "latest", return_value=snapshot):
            live_effort = self.app._activity.live_effort()
            assert live_effort is not None
            self.assertGreater(live_effort, .9)
            self.app.settings.observe_computer = False
            self.assertIsNone(self.app._activity.live_effort())
            self.app.settings.observe_computer = True
        stale = ComputerSnapshot(cpu=100, measured_at=time.monotonic() - 100)
        with patch.object(self.app.activity_monitor, "latest", return_value=stale):
            self.assertIsNone(self.app._activity.live_effort())

    def test_settings_lifetime_is_independent_of_toolbar(self):
        self.toolbar.settings_button.invoke()
        window = self.app._hover.settings_window
        assert window is not None
        self.app._hover.dismiss_outside(-999, -999)
        self.assertFalse(self.toolbar.visible)
        self.assertIs(self.app._hover.settings_window, window)
        window.close()
        self.assertIsNone(self.app._hover.settings_window)


if __name__ == "__main__":
    unittest.main()
