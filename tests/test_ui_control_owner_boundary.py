"""Controls remain one implementation across migration imports."""

import unittest

from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.food_menu import FoodMenu
from aiko_pet.ui.windows.settings_window import SettingsWindow


class ControlOwnerBoundaryTests(unittest.TestCase):
    def test_windows_have_one_canonical_implementation(self) -> None:
        for cls in (ActionToolbar, FoodMenu, SettingsWindow):
            self.assertTrue(cls.__module__.startswith("aiko_pet.ui.windows."))
