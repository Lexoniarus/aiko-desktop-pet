"""The desktop shell uses the components that own behavior and state."""

import unittest
from pathlib import Path


class DesktopBoundaryTests(unittest.TestCase):
    def test_desktop_shell_uses_owners_not_legacy_reads(self) -> None:
        source = (
            Path(__file__).resolve().parents[1] / "aiko_pet" / "gui.py"
        ).read_text("utf-8")
        forbidden = (
            "self.toolbar", "self.status_panel", "self.settings_popup",
            "self._bubble", "self._walk_remaining", "self._next_walk",
            "self._last_spoken", "self._last_saved", "self._last_hover",
            "self._refresh_status()", "self._show_emote(", "self.say(",
            "self._move_bubble()", "self._placed", "self._gaze_sector",
        )
        for expression in forbidden:
            with self.subTest(expression=expression):
                self.assertNotIn(expression, source)


if __name__ == "__main__":
    unittest.main()
