"""World definitions reference canonical food and asset records without copy."""

from __future__ import annotations

import unittest
from dataclasses import replace
from types import MappingProxyType

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.world_catalog import build_food_object_definitions
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.world.contracts import ObjectFootprint, ObjectInteraction, WorldSurface
from aiko_pet.world.state import WorldState


class WorldCatalogTests(unittest.TestCase):
    def test_real_catalogs_supply_food_and_graphics_by_canonical_id(self) -> None:
        items = load_item_catalog()
        definitions = build_food_object_definitions(DEFAULT_CATALOG, items)
        self.assertEqual({item.definition_id for item in definitions},
                         set(DEFAULT_CATALOG.foods))
        self.assertNotIn("energy_drink", {item.definition_id for item in definitions})
        world = WorldState(WorldSurface(800, 600), definitions)
        for definition in definitions:
            with self.subTest(food=definition.food_id):
                self.assertEqual(definition.food_id, definition.definition_id)
                self.assertEqual(definition.asset_id, definition.definition_id)
                self.assertEqual(definition.interactions,
                                 frozenset((ObjectInteraction.EAT,)))
                portion = world.place_resting(definition.definition_id, 100,
                                              ObjectFootprint(8, 8))
                self.assertEqual(portion.definition_id, definition.definition_id)

    def test_missing_or_mismatched_asset_identity_is_rejected(self) -> None:
        items = load_item_catalog()
        missing = dict(items.foods)
        del missing["onigiri"]
        mismatch = dict(items.foods)
        mismatch["onigiri"] = replace(items.foods["onigiri"], key="apple")
        for foods in (missing, mismatch):
            with self.subTest(keys=tuple(foods)):
                with self.assertRaises(ValueError):
                    build_food_object_definitions(
                        DEFAULT_CATALOG, replace(items, foods=MappingProxyType(foods)),
                    )

    def test_mismatched_nutrition_identity_is_rejected(self) -> None:
        foods = dict(DEFAULT_CATALOG.foods)
        foods["onigiri"] = replace(foods["onigiri"], id="apple")
        with self.assertRaises(ValueError):
            build_food_object_definitions(
                replace(DEFAULT_CATALOG, foods=MappingProxyType(foods)),
                load_item_catalog(),
            )
