"""Validate the prepared menu/hand asset contract without Pillow."""

from __future__ import annotations

import json
import struct
from pathlib import Path
import unittest

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.food import FOOD_CATALOG, FOOD_MENU_ORDER
from aiko_pet.pet.content import GERMAN_TEXT
from aiko_pet.ui.view_models.food_models import food_choices


class PreparedFoodCatalogTests(unittest.TestCase):
    def test_all_foods_have_one_nutrition_entry_and_one_visual(self) -> None:
        items = load_item_catalog()
        choices = food_choices(items)
        ids = tuple(choice.id for choice in choices)
        self.assertEqual(len(ids), 11)
        self.assertEqual(len(set(ids)), 11)
        self.assertEqual(ids, FOOD_MENU_ORDER)
        self.assertEqual(set(ids), set(items.foods))
        choice_by_id = {choice.id: choice for choice in choices}
        for item_id, item in items.foods.items():
            self.assertEqual(choice_by_id[item_id].image_path, item.icon)
            self.assertEqual(choice_by_id[item_id].name, item.label)
            expected_name = (
                GERMAN_TEXT.format("ui.energy_drink_name")
                if item_id == "energy_drink"
                else FOOD_CATALOG[item_id].display_name
            )
            self.assertEqual(item.label, expected_name)
        self.assertEqual(set(FOOD_CATALOG), set(items.foods) - {"energy_drink"})
        self.assertEqual(tuple(items.weapons), ("sword",))
        for key, item in items.foods.items():
            self.assertEqual(
                item.care_action,
                "energy_drink" if key == "energy_drink" else "feed",
            )

    def test_asset_manifest_does_not_duplicate_food_titles(self) -> None:
        path = (
            Path(__file__).resolve().parents[1] / "aiko_pet" / "assets"
            / "items" / "items.json"
        )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(all("label" not in row for row in data["foods"]))
        self.assertTrue(all("label" in row for row in data["weapons"]))

    def test_prepared_pngs_and_grips(self) -> None:
        items = load_item_catalog()
        png_magic = bytes((137, 80, 78, 71, 13, 10, 26, 10))
        for item in (*items.foods.values(), *items.weapons.values()):
            with self.subTest(item=item.key):
                self.assertEqual(set(item.sprites), {1, 2})
                for sprite in item.sprites.values():
                    with sprite.path.open("rb") as file:
                        header = file.read(24)
                    self.assertEqual(header[:8], png_magic)
                    width, height = struct.unpack(">II", header[16:24])
                    self.assertTrue(0 <= sprite.pivot[0] <= width)
                    self.assertTrue(0 <= sprite.pivot[1] <= height)
                self.assertNotEqual(
                    item.sprites[1].path.read_bytes(),
                    item.sprites[2].path.read_bytes(),
                )
                if item.icon is not None:
                    with item.icon.open("rb") as file:
                        header = file.read(24)
                    self.assertEqual(struct.unpack(">II", header[16:24]), (64, 64))

    def test_prepared_native_sizes(self) -> None:
        expected = {
            "energy_drink": ((20, 44), (40, 88)),
            "donut": ((37, 33), (74, 66)),
            "cookie": ((33, 33), (66, 66)),
            "melonpan": ((37, 32), (74, 64)),
            "cupcake": ((29, 38), (58, 76)),
            "dorayaki": ((37, 31), (74, 62)),
        }
        foods = load_item_catalog().foods
        for key, sizes in expected.items():
            for scale, expected_size in enumerate(sizes, 1):
                with foods[key].sprites[scale].path.open("rb") as file:
                    header = file.read(24)
                self.assertEqual(
                    struct.unpack(">II", header[16:24]), expected_size,
                )


if __name__ == "__main__":
    unittest.main()
