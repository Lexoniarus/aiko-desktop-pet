"""Canonical gaze contract remains identical to its previous public import."""

import unittest

from aiko_pet.pet.animation.gaze import gaze_sector
from aiko_pet.presentation.gaze import gaze_sector as legacy_gaze_sector


class PetGazeBoundaryTests(unittest.TestCase):
    def test_legacy_gaze_is_same_implementation(self) -> None:
        self.assertIs(gaze_sector, legacy_gaze_sector)

    def test_gaze_preserves_distance_and_direction(self) -> None:
        self.assertIsNone(gaze_sector(0, 0, 0, 0))
        self.assertEqual(gaze_sector(0, 0, 0, -100), 0)
        self.assertEqual(gaze_sector(0, 0, 100, 0), 4)

