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

if __name__ == "__main__":
    unittest.main()
