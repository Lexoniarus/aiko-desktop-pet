"""Consumption kinds, put-down and atomic surface reconfiguration."""

import unittest

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.world.contracts import ObjectFootprint, ObjectState, WorldSurface
from aiko_pet.world.state import WorldOperationError, WorldState


class WorldExtensionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.world = WorldState(WorldSurface(800, 600), build_consumable_definitions(
            DEFAULT_CATALOG, load_item_catalog(),
        ))

    def test_drink_and_food_use_distinct_definitions(self) -> None:
        drink = self.world.place_resting("energy_drink", 100, ObjectFootprint(8, 8))
        held = self.world.collect_resting(drink.instance_id, expected_revision=0)
        consumed = self.world.consume(held.instance_id, expected_revision=held.revision)
        self.assertEqual(consumed.state, ObjectState.CONSUMED)

    def test_put_down_changes_custody_without_recreating_a_portion(self) -> None:
        item = self.world.place_resting("onigiri", 100, ObjectFootprint(8, 8))
        held = self.world.collect_resting(item.instance_id, expected_revision=0)
        down = self.world.put_down(item.instance_id, 200,
                                   expected_revision=held.revision)
        self.assertEqual(down.state, ObjectState.RESTING)
        self.assertEqual(down.instance_id, item.instance_id)
        self.assertEqual(len(self.world.snapshot().objects), 1)

    def test_surface_resize_invalidates_moved_anchors_and_keeps_old_snapshot(self):
        item = self.world.place_resting("onigiri", 700, ObjectFootprint(8, 8))
        before = self.world.snapshot()
        self.world.change_surface(WorldSurface(400, 500))
        moved = self.world.get(item.instance_id)
        assert moved.position is not None
        self.assertEqual(moved.position.x, 392)
        self.assertGreater(moved.revision, item.revision)
        self.assertEqual(before.surface.width, 800)

    def test_invalid_resize_does_not_partly_move_items(self):
        self.world.place_resting("onigiri", 100, ObjectFootprint(80, 80))
        before = self.world.snapshot()
        with self.assertRaises(WorldOperationError):
            self.world.change_surface(WorldSurface(100, 500))
        self.assertEqual(self.world.snapshot(), before)
