"""World motion is elapsed-time driven and rests only after the rebound tail."""

import unittest

from aiko_pet.infrastructure.world_motion import motion_parameters
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldOperationError, WorldState


class WorldFallingTests(unittest.TestCase):
    def make(self):
        world = WorldState(WorldSurface(800, 800), (ObjectDefinition("toy", "toy"),))
        item = world.create_held("toy", WorldPosition(100, 600), ObjectFootprint(8, 8))
        world.release(item.instance_id, expected_revision=0)
        return world, item.instance_id

    def test_equivalent_elapsed_time_and_idempotent_settlement(self):
        first, token = self.make()
        second, other = self.make()
        first.advance_motion(0.5, motion_parameters())
        for _ in range(5):
            second.advance_motion(0.1, motion_parameters())
        a, b = first.get(token), second.get(other)
        assert a.position is not None and b.position is not None
        self.assertAlmostEqual(a.position.height, b.position.height)
        first.advance_motion(10, motion_parameters())
        landed = first.get(token)
        self.assertEqual(landed.state, ObjectState.RESTING)
        first.advance_motion(10, motion_parameters())
        self.assertEqual(first.get(token), landed)

    def test_rebounds_are_not_collectible_and_checkpoint_restores_velocity(self):
        world, token = self.make()
        world.change_surface(WorldSurface(800, 800, 96))
        world.advance_motion(1.2, motion_parameters())
        bounced = world.get(token)
        self.assertEqual(bounced.state, ObjectState.BOUNCING)
        assert bounced.motion is not None
        self.assertGreater(bounced.motion.vy, 0)
        with self.assertRaises(WorldOperationError):
            world.collect_resting(token, expected_revision=bounced.revision)
        saved = world.snapshot()
        world.advance_motion(.1, motion_parameters())
        expected = world.get(token)
        world.restore_snapshot(saved)
        world.advance_motion(.1, motion_parameters())
        self.assertEqual(world.get(token), expected)
        before = world.snapshot()
        for elapsed in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                world.advance_motion(elapsed, motion_parameters())
            self.assertEqual(world.snapshot(), before)

    def test_outside_release_finishes_on_reachable_ground_and_can_be_removed(self):
        world, token = self.make()
        world.change_surface(WorldSurface(800, 800, 192))
        world.advance_motion(1.2, motion_parameters())
        checkpoint = world.snapshot()
        bouncing = world.get(token)
        world.remove(token, expected_revision=bouncing.revision)
        self.assertIsNone(world.get(token).motion)
        world.restore_snapshot(checkpoint)
        world.advance_motion(20, motion_parameters())
        item = world.get(token)
        assert item.position is not None
        self.assertEqual(item.state, ObjectState.RESTING)
        self.assertGreaterEqual(item.position.x, 192)
        self.assertIsNone(item.motion)
