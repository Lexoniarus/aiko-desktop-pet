"""Legacy sprite utility modules point to one pet-view implementation."""

import unittest

from aiko_pet.ui.pet_view.character_sprite_cache import CharacterSpriteCache
from aiko_pet.ui.character_sprite_cache import (
    CharacterSpriteCache as LegacySpriteCache,
)
from aiko_pet.ui.pet_view.food_overlay import FoodOverlay
from aiko_pet.ui.food_overlay import FoodOverlay as LegacyFoodOverlay
from aiko_pet.ui.pet_view.rest_pose_renderer import RestPoseRenderer
from aiko_pet.ui.rest_pose_renderer import RestPoseRenderer as LegacyRestPose


class PetViewHelperTests(unittest.TestCase):
    def test_compatibility_identity(self) -> None:
        self.assertIs(CharacterSpriteCache, LegacySpriteCache)
        self.assertIs(FoodOverlay, LegacyFoodOverlay)
        self.assertIs(RestPoseRenderer, LegacyRestPose)
