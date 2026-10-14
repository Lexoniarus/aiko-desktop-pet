"""Legacy sprite utility modules point to one pet-view implementation."""

import unittest

from aiko_pet.ui.pet_view.character_sprite_cache import CharacterSpriteCache
from aiko_pet.ui.pet_view.food_overlay import FoodOverlay
from aiko_pet.ui.pet_view.rest_pose_renderer import RestPoseRenderer


class PetViewHelperTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        for cls in (CharacterSpriteCache, FoodOverlay, RestPoseRenderer):
            self.assertTrue(cls.__module__.startswith("aiko_pet.ui.pet_view."))
