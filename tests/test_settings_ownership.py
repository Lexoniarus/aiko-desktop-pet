"""Behaviour and desktop settings have distinct, single state owners."""

from __future__ import annotations

import unittest

from aiko_pet.application.settings import (
    DesktopDisplaySettings,
    PetBehaviorSettings,
    PetSettings,
)


class SettingsOwnershipTests(unittest.TestCase):
    def test_aggregate_composes_distinct_mutable_options(self) -> None:
        settings = PetSettings(x=420, auto_walk=False)
        self.assertIsInstance(settings.desktop, DesktopDisplaySettings)
        self.assertIsInstance(settings.behavior, PetBehaviorSettings)
        self.assertEqual(settings.desktop.x, 420)
        self.assertFalse(settings.behavior.auto_walk)
        settings.desktop.x = 500
        settings.behavior.auto_walk = True
        self.assertEqual(settings.x, 500)
        self.assertTrue(settings.auto_walk)
        settings.x = 600
        settings.auto_walk = False
        self.assertEqual(settings.desktop.x, 600)
        self.assertFalse(settings.behavior.auto_walk)

    def test_flat_save_format_and_roundtrip_remain_identical(self) -> None:
        settings = PetSettings(
            x=100, y=200, scale=2, always_on_top=False,
            auto_walk=False, auto_routine=False, follow_cursor=False,
            spontaneous_talk=False, observe_computer=False,
            learn_rhythm=False, toolbar_x=44, toolbar_y=55,
        )
        self.assertEqual(
            list(settings.to_dict()),
            [
                "x", "y", "scale", "always_on_top", "auto_walk",
                "auto_routine", "follow_cursor", "spontaneous_talk",
                "observe_computer", "learn_rhythm", "toolbar_x",
                "toolbar_y", "online_social",
            ],
        )
        self.assertEqual(PetSettings.from_dict(settings.to_dict()), settings)
        self.assertEqual(PetSettings().to_dict()["scale"], 1)


if __name__ == "__main__":
    unittest.main()
