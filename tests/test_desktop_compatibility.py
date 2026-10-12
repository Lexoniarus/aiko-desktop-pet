"""The legacy API is a typed facade, not part of the new application core."""

import unittest

from aiko_pet.desktop.compatibility import DesktopCompatibility
from aiko_pet.gui import DesktopPet


class DesktopCompatibilityTests(unittest.TestCase):
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
