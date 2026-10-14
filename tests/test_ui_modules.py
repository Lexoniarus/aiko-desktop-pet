"""Module ownership for the single toolbar and persistent utility windows."""

import unittest
from pathlib import Path

from aiko_pet.asset_paths import EMOTE_IMAGE_DIR, KENNEY_UI_DIR, SPRITE_FRAME_DIR
from aiko_pet.ui.action_toolbar import ActionToolbar
from aiko_pet.ui.settings_window import SettingsWindow
from aiko_pet.ui.toolbar_details import ToolbarDetails
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.common.window_drag import WindowDrag


class UiModuleExtractionTests(unittest.TestCase):
    def test_canonical_asset_directories_exist(self) -> None:
        for directory in (SPRITE_FRAME_DIR, EMOTE_IMAGE_DIR, KENNEY_UI_DIR):
            with self.subTest(directory=directory):
                self.assertTrue(directory.is_dir())

    def test_view_components_have_distinct_module_ownership(self) -> None:
        for component, module in (
            (ActionToolbar, "action_toolbar"),
            (SettingsWindow, "settings_window"),
            (ToolbarDetails, "toolbar_details"),
            (AikoSkin, "common.skin"), (WindowDrag, "common.window_drag"),
        ):
            self.assertEqual(component.__module__, f"aiko_pet.ui.{module}")

    def test_redundant_status_window_and_popup_are_removed(self) -> None:
        ui = Path(__file__).resolve().parents[1] / "aiko_pet" / "ui"
        for name in ("status_panel.py", "status_contracts.py", "settings_popup.py"):
            self.assertFalse((ui / name).exists(), name)


if __name__ == "__main__":
    unittest.main()
