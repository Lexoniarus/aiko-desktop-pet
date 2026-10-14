"""Controls remain one implementation across migration imports."""

import unittest

from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.action_toolbar import ActionToolbar as LegacyToolbar
from aiko_pet.ui.windows.food_menu import FoodMenu
from aiko_pet.ui.food_menu import FoodMenu as LegacyFoodMenu
from aiko_pet.ui.windows.settings_window import SettingsWindow
from aiko_pet.ui.settings_window import SettingsWindow as LegacySettingsWindow


class ControlOwnerBoundaryTests(unittest.TestCase):
    def test_windows_have_one_canonical_implementation(self) -> None:
        self.assertIs(ActionToolbar, LegacyToolbar)
        self.assertIs(FoodMenu, LegacyFoodMenu)
        self.assertIs(SettingsWindow, LegacySettingsWindow)
