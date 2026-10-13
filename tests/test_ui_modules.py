"""Regression contracts for extracting the Tkinter view modules."""

import unittest

from aiko_pet import gui
from aiko_pet.asset_paths import EMOTE_IMAGE_DIR, KENNEY_UI_DIR, SPRITE_FRAME_DIR
from aiko_pet.ui.action_toolbar import ActionToolbar
from aiko_pet.ui.settings_popup import SettingsPopup
from aiko_pet.ui.status_panel import StatusPanel


class UiModuleExtractionTests(unittest.TestCase):
    def test_existing_gui_imports_preserve_public_widget_classes(self) -> None:
        self.assertIs(gui.ActionToolbar, ActionToolbar)
        self.assertIs(gui.SettingsPopup, SettingsPopup)
        self.assertIs(gui.StatusPanel, StatusPanel)

    def test_legacy_asset_paths_resolve_to_canonical_directories(self) -> None:
        self.assertEqual(gui.ASSETS, SPRITE_FRAME_DIR)
        self.assertEqual(gui.EMOTE_ASSETS, EMOTE_IMAGE_DIR)
        self.assertEqual(gui.SCI_FI_UI, KENNEY_UI_DIR)
        for directory in (SPRITE_FRAME_DIR, EMOTE_IMAGE_DIR, KENNEY_UI_DIR):
            with self.subTest(directory=directory):
                self.assertTrue(directory.is_dir())

    def test_view_components_have_distinct_module_ownership(self) -> None:
        self.assertEqual(ActionToolbar.__module__, "aiko_pet.ui.action_toolbar")
        self.assertEqual(StatusPanel.__module__, "aiko_pet.ui.status_panel")
        self.assertEqual(SettingsPopup.__module__, "aiko_pet.ui.settings_popup")


if __name__ == "__main__":
    unittest.main()
