"""The legacy API is a typed facade, not part of the new application core."""

import unittest
from pathlib import Path

from aiko_pet.desktop.compatibility import DesktopCompatibility
from aiko_pet.gui import DesktopPet


class DesktopCompatibilityTests(unittest.TestCase):
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

    def test_desktop_shell_inherits_only_the_explicit_facade(self) -> None:
        self.assertTrue(issubclass(DesktopPet, DesktopCompatibility))
        for member in (
            "toolbar", "settings_popup", "_bubble", "_next_comment",
            "_last_hardware_sample", "_walk_remaining", "_placed",
            "_maybe_walk", "_live_effort", "_render_current_sprite",
        ):
            with self.subTest(member=member):
                self.assertIn(member, vars(DesktopCompatibility))


if __name__ == "__main__":
    unittest.main()
