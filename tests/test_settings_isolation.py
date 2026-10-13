"""Settings window works without DesktopPet or direct state references."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.ui.settings_contracts import SettingsActions, SettingsSnapshot
from aiko_pet.ui.settings_popup import SettingsPopup


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
        self.events: list[str] = []
        self.popup = SettingsPopup(
            self.root, 400, 180,
            snapshot=SettingsSnapshot(
                scale=1,
                options=(
                    ("always_on_top", True), ("auto_walk", True),
                    ("auto_routine", True), ("follow_cursor", True),
                    ("spontaneous_talk", True), ("observe_computer", True),
                    ("learn_rhythm", False),
                ),
            ),
            actions=SettingsActions(
                open_status=lambda: self.events.append("status"),
                toggle_scale=lambda: self.events.append("scale"),
                set_option=lambda key, value: self.events.append(
                    f"{key}:{value}",
                ),
                forget_rhythm=lambda: None,
                reset_toolbar=lambda: None,
                center=lambda: None,
                quit=lambda: self.events.append("quit"),
                closed=lambda: self.events.append("closed"),
            ),
            toolbar_y=lambda: None, always_on_top=False,
        )
        self.addCleanup(self.root.destroy)

    def test_checkbox_uses_narrow_action_port(self) -> None:
        self.assertFalse(hasattr(self.popup, "pet"))
        self.popup.values["auto_walk"].set(False)
        self.popup._apply_setting("auto_walk", self.popup.values["auto_walk"])
        self.assertEqual(self.events, ["auto_walk:False"])

    def test_close_reports_lifecycle_event(self) -> None:
        self.popup.close()
        self.assertEqual(self.events, ["closed"])


if __name__ == "__main__":
    unittest.main()
