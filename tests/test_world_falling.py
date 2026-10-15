"""Falling depends on elapsed time and lands once at the original x."""

import unittest

from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class WorldFallingTests(unittest.TestCase):
    def make(self):
        world = WorldState(WorldSurface(800, 800), (ObjectDefinition("toy", "toy"),))
        item = world.create_held("toy", WorldPosition(100, 600), ObjectFootprint(8, 8))
        world.release(item.instance_id, expected_revision=0)
        return world, item.instance_id

    def test_equivalent_elapsed_time_and_one_ground_contact(self):
        first, token = self.make()
        second, other = self.make()
        first.advance_falls(0.5, gravity=900)
        for _ in range(5):
            second.advance_falls(0.1, gravity=900)
        a, b = first.get(token), second.get(other)
        assert a.position is not None and b.position is not None
        self.assertAlmostEqual(a.position.height, b.position.height)
        first.advance_falls(10, gravity=900)
        landed = first.get(token)
        self.assertEqual(landed.state, ObjectState.RESTING)
        first.advance_falls(10, gravity=900)
        self.assertEqual(first.get(token), landed)
