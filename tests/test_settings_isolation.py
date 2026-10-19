"""Persistent settings own only controls; all preferences use narrow ports."""

from __future__ import annotations

import tkinter as tk
import unittest
from dataclasses import replace

from aiko_pet.ui.view_models.contracts import SettingsSnapshot
from aiko_pet.ui.windows.settings_contracts import SettingsActions
from aiko_pet.ui.windows.settings_window import SettingsWindow


class StandaloneSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No Tk display") from error
        probe.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.events: list[str] = []
        self.view = SettingsSnapshot(
            scale=1,
            options=(
                ("always_on_top", True), ("auto_walk", True),
                ("auto_routine", True), ("follow_cursor", True),
                ("spontaneous_talk", True), ("observe_computer", True),
                ("learn_rhythm", False), ("online_social", False),
            ),
        )
        self.window = SettingsWindow(
            self.root, 600, 180, snapshot=lambda: self.view,
            actions=SettingsActions(
                toggle_scale=self.toggle_scale,
                set_option=lambda key, value: self.events.append(
                    f"{key}:{value}",
                ),
                forget_rhythm=lambda: self.events.append("forget"),
                reset_toolbar=lambda: self.events.append("reset"),
                center=lambda: self.events.append("center"),
                quit=lambda: self.events.append("quit"),
                closed=lambda: self.events.append("closed"),
            ),
            always_on_top=False,
        )
        self.root.update_idletasks()
        self.addCleanup(self.window.close)

    def toggle_scale(self) -> None:
        self.events.append("scale")
        self.view = replace(self.view, scale=2 if self.view.scale == 1 else 1)

    def test_checkbox_uses_narrow_action_port(self) -> None:
        self.assertFalse(hasattr(self.window, "pet"))
        self.window.checkbuttons["auto_walk"].invoke()
        self.assertEqual(self.events, ["auto_walk:False"])
        self.assertTrue(self.window.window.winfo_exists())

    def test_close_notifies_exactly_once(self) -> None:
        self.window.close()
        self.window.close()
        self.assertEqual(self.events, ["closed"])

    def test_all_non_quit_commands_keep_window_open(self) -> None:
        for button in (
            self.window.scale_button, self.window.forget_button,
            self.window.reset_button, self.window.center_button,
        ):
            button.invoke()
            self.assertTrue(self.window.window.winfo_exists())
        self.assertEqual(self.events, ["scale", "forget", "reset", "center"])
        self.assertIn("2×", self.window.scale_button.cget("text"))

    def test_external_snapshot_refresh_does_not_send_commands(self) -> None:
        self.view = replace(
            self.view, scale=2,
            options=tuple((key, not value) for key, value in self.view.options),
        )
        self.window.refresh()
        self.window.refresh()
        self.assertEqual(self.events, [])
        for key, value in self.view.options:
            self.assertEqual(self.window.values[key].get(), value)
        self.assertIn("2×", self.window.scale_button.cget("text"))

    def test_header_drag_changes_only_own_position(self) -> None:
        before = (self.root.winfo_x(), self.root.winfo_y())
        self.window.window.geometry("+40+50")
        self.root.update_idletasks()
        start = tk.Event()
        start.x_root, start.y_root = 60, 60
        self.window._drag.start(start)
        motion = tk.Event()
        motion.x_root, motion.y_root = 100, 100
        self.window._drag.move(motion)
        self.window._drag.finish(motion)
        self.root.update_idletasks()
        self.assertEqual(self.window.position, (80, 90))
        self.assertEqual(before, (self.root.winfo_x(), self.root.winfo_y()))
        self.window.refresh()
        self.root.update_idletasks()
        self.assertEqual(self.window.window.winfo_rootx(), 80)
        self.assertEqual(self.window.window.winfo_rooty(), 90)
        self.assertEqual(self.events, [])

    def test_idle_open_window_is_not_an_interaction(self) -> None:
        self.assertFalse(self.window.interacting(-999, -999, 1000))
        x, y = self.window.window.winfo_rootx(), self.window.window.winfo_rooty()
        self.assertTrue(self.window.interacting(x + 5, y + 5, 1000))

    def test_close_during_drag_cleans_up_once(self) -> None:
        event = tk.Event()
        event.x_root, event.y_root = 40, 50
        self.window._drag.start(event)
        self.window.close()
        self.window._drag.move(event)
        self.window._drag.finish(event)
        self.window.close()
        self.assertEqual(self.events, ["closed"])

    def test_saved_session_position_is_clamped_on_reopen(self) -> None:
        self.window.close()
        other = SettingsWindow(
            self.root, 0, 0, snapshot=lambda: self.view,
            actions=self.window._actions, always_on_top=False,
            skin=self.window.skin, position=(-900, -900),
        )
        self.addCleanup(other.close)
        self.assertEqual(other.position, (0, 0))


if __name__ == "__main__":
    unittest.main()
