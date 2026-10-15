"""Canonical gaze contract remains identical to its previous public import."""

import unittest

from aiko_pet.pet.animation.gaze import gaze_sector


class PetGazeBoundaryTests(unittest.TestCase):
    def test_gaze_implementation_has_one_pet_owner(self) -> None:
        self.assertEqual(gaze_sector.__module__, "aiko_pet.pet.animation.gaze")

    def test_gaze_preserves_distance_and_direction(self) -> None:
        self.assertIsNone(gaze_sector(0, 0, 0, 0))
        self.assertEqual(gaze_sector(0, 0, 0, -100), 0)
        self.assertEqual(gaze_sector(0, 0, 100, 0), 4)
