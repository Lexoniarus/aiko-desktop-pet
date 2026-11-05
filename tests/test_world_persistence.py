"""Joint snapshots preserve old saves and normalize interrupted World items."""

import unittest

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.infrastructure.world_codec import decode_world, encode_world
from aiko_pet.infrastructure.world_motion import motion_parameters
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.world.contracts import (
    ObjectFootprint,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class WorldPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.definitions = build_consumable_definitions(DEFAULT_CATALOG,
                                                       load_item_catalog())
        self.world = WorldState(WorldSurface(800, 600), self.definitions)

    def test_bouncing_save_recovers_a_safe_target_without_resuming_motion(self):
        self.world.change_surface(WorldSurface(800, 600, 96))
        item = self.world.create_held("apple", WorldPosition(8, 300),
                                       ObjectFootprint(8, 8))
        self.world.release(item.instance_id, expected_revision=0)
        self.world.advance_motion(.9, motion_parameters())
        self.assertEqual(self.world.get(item.instance_id).state, ObjectState.BOUNCING)
        saved = encode_world(self.world.snapshot(), recovery_x=400)
        restored = decode_world(saved, self.definitions).objects[0]
        self.assertEqual(restored.state, ObjectState.RESTING)
        self.assertIsNone(restored.motion)
        assert restored.position is not None
        self.assertGreaterEqual(restored.position.x, 96)

    def test_transient_items_restore_on_ground_without_reused_terminal_ids(self):
        first = self.world.create_held("apple", WorldPosition(100, 300),
                                       ObjectFootprint(8, 8))
        self.world.release(first.instance_id, expected_revision=0)
        second = self.world.create_held("energy_drink", WorldPosition(200, 300),
                                        ObjectFootprint(8, 8))
        held = self.world.accept_handover_on_release(second.instance_id,
                                                    expected_revision=0)
        saved = encode_world(self.world.snapshot(), recovery_x=250)
        recovered = decode_world(saved, self.definitions)
        self.assertTrue(all(item.state == ObjectState.RESTING
                            for item in recovered.objects))
        restored = WorldState(recovered.surface, self.definitions)
        restored.restore_snapshot(recovered)
        next_item = restored.place_resting("apple", 300, ObjectFootprint(8, 8))
        self.assertNotIn(next_item.instance_id, (first.instance_id, held.instance_id))
