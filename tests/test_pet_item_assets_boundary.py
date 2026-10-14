"""Handheld-item metadata has one canonical pet contract."""

import unittest

from aiko_pet.pet.animation.item_assets import ItemCatalog, ItemSprite


class PetItemAssetBoundaryTests(unittest.TestCase):
    def test_original_imports_share_identity(self) -> None:
        self.assertEqual(ItemCatalog.__module__, "aiko_pet.pet.animation.item_assets")
        self.assertEqual(ItemSprite.__module__, "aiko_pet.pet.animation.item_assets")
