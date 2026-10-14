"""Pet animation policy classes preserve existing canonical behaviour."""

import unittest

from aiko_pet.pet.animation.animation import FrameClock, SpriteSelection
from aiko_pet.presentation.animation import FrameClock as LegacyFrameClock
from aiko_pet.presentation.animation import SpriteSelection as LegacySpriteSelection
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.presentation.ambient import AmbientDirector as LegacyAmbient


class PetAnimationPolicyBoundaryTests(unittest.TestCase):
    def test_previous_imports_are_same_objects(self) -> None:
        self.assertIs(FrameClock, LegacyFrameClock)
        self.assertIs(SpriteSelection, LegacySpriteSelection)
        self.assertIs(AmbientDirector, LegacyAmbient)
