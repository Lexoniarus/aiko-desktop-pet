"""Runtime item sprites expose their original and prepared display paths."""

import unittest

from aiko_pet.infrastructure.item_assets import load_item_catalog


class ItemDisplayAssetsTests(unittest.TestCase):
    def test_catalog_exposes_distinct_original_and_display_paths(self):
        for item in load_item_catalog().foods.values():
            for sprite in item.sprites.values():
                self.assertIsNotNone(sprite.display_path)
                self.assertNotEqual(sprite.path, sprite.display_path)
