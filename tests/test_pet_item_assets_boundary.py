"""Handheld-item metadata has one canonical pet contract."""

import unittest

from aiko_pet.pet.animation.item_assets import ItemCatalog, ItemSprite
from aiko_pet.presentation.item_assets import ItemCatalog as LegacyCatalog
from aiko_pet.presentation.item_assets import ItemSprite as LegacySprite


class PetItemAssetBoundaryTests(unittest.TestCase):
    def test_original_imports_share_identity(self) -> None:
        self.assertIs(ItemCatalog, LegacyCatalog)
        self.assertIs(ItemSprite, LegacySprite)
