"""Application-owned preferences preserve saved defaults and validation."""

from __future__ import annotations

import unittest

from aiko_pet.application.settings import PetSettings


class PetSettingsModelTests(unittest.TestCase):
    def test_existing_settings_schema_and_defaults_are_unchanged(self) -> None:
        settings = PetSettings()
        self.assertEqual(
            settings.to_dict(),
            {
                "x": None,
                "y": None,
                "scale": 1,
                "always_on_top": True,
                "auto_walk": True,
                "auto_routine": True,
                "follow_cursor": True,
                "spontaneous_talk": True,
                "observe_computer": True,
                "learn_rhythm": True,
                "toolbar_x": None,
                "toolbar_y": None,
            },
        )

    def test_invalid_coordinates_and_settings_use_legacy_fallbacks(self) -> None:
        raw = {
            "x": True,
            "y": 30_000,
            "scale": 5,
            "always_on_top": False,
            "auto_routine": False,
            "toolbar_x": 17,
            "toolbar_y": None,
        }
        settings = PetSettings.from_dict(raw)
        self.assertIsNone(settings.x)
        self.assertIsNone(settings.y)
        self.assertEqual(settings.scale, 1)
        self.assertFalse(settings.always_on_top)
        self.assertFalse(settings.auto_routine)
        self.assertEqual(settings.toolbar_x, 17)
        self.assertIsNone(settings.toolbar_y)
        self.assertEqual(PetSettings.from_dict(settings.to_dict()), settings)


if __name__ == "__main__":
    unittest.main()
