"""Pet animation policy classes preserve existing canonical behaviour."""

import unittest

from aiko_pet.pet.animation.animation import FrameClock, SpriteSelection
from aiko_pet.pet.animation.ambient import AmbientDirector


class PetAnimationPolicyBoundaryTests(unittest.TestCase):
    def test_previous_imports_are_same_objects(self) -> None:
        self.assertEqual(FrameClock.__module__, "aiko_pet.pet.animation.animation")
        self.assertEqual(SpriteSelection.__module__, "aiko_pet.pet.animation.animation")
        self.assertEqual(AmbientDirector.__module__, "aiko_pet.pet.animation.ambient")
