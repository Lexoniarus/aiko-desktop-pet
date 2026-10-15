"""Food nutrition and menu records are data, not hardcoded in pet policy."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import cast

from aiko_pet.pet.food import DEFAULT_FOOD_ID, FOOD_CATALOG, FOOD_MENU_ORDER
from aiko_pet.pet.food_catalog import (
    FoodProfile,
    load_packaged_food_catalog,
    parse_food_catalog,
)


class FoodCatalogDataTests(unittest.TestCase):
    def test_packaged_json_matches_runtime_food_profiles(self) -> None:
        source = (
            Path(__file__).resolve().parents[1]
            / "aiko_pet" / "data" / "food_catalog.json"
        )
        loaded = parse_food_catalog(json.loads(source.read_text("utf-8")))
        self.assertEqual(dict(loaded.foods), dict(FOOD_CATALOG))
        self.assertEqual(loaded.default_food_id, DEFAULT_FOOD_ID)
        self.assertEqual(loaded.menu_order, FOOD_MENU_ORDER)
        self.assertEqual(load_packaged_food_catalog(), loaded)
        with self.assertRaises(TypeError):
            cast(dict[str, FoodProfile], loaded.foods)["new"] = (
                next(iter(loaded.foods.values()))
            )

    def test_bad_values_and_duplicate_ids_are_rejected(self) -> None:
        good = {
            "version": 1, "default_food_id": "apple",
            "menu_order": ["apple", "energy_drink"],
            "foods": [{
                "id": "apple", "display_name": "Apfel",
                "category": "snack", "instant_satiety_points": 14,
                "digest_reserve_minutes": 38, "normal_mood_bonus": 3,
            }],
        }
        self.assertEqual(parse_food_catalog(good).foods["apple"].display_name,
                         "Apfel")
        for bad in (
            {**good, "version": 2},
            {**good, "foods": []},
            {**good, "foods": [*good["foods"], *good["foods"]]},
            {**good, "menu_order": ["apple"]},
            {**good, "default_food_id": "missing"},
            {**good, "foods": [{**good["foods"][0],
                                "normal_mood_bonus": float("nan")}]},
            {**good, "foods": [{**good["foods"][0],
                                "digest_reserve_minutes": True}]},
        ):
            with self.subTest(data=bad):
                with self.assertRaises(ValueError):
                    parse_food_catalog(bad)
