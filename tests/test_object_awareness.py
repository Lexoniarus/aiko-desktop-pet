"""Real World snapshots do not bypass recognition or remembered positions."""

import unittest

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectAwarenessTests(unittest.TestCase):
    def test_hidden_relocation_does_not_update_subjective_goal(self):
        world = WorldState(WorldSurface(2000, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for now in (0, 0.3, 0.7):
            goal = awareness.update(world.snapshot(), state, now=now, x=0,
                                    height=0, width=192, attentive=True, blocked=False)
        assert goal is not None
        world.move_resting(item.instance_id, 1500, expected_revision=0)
        goal = awareness.update(world.snapshot(), state, now=2, x=0,
                                height=0, width=192, attentive=True, blocked=False)
        assert goal is not None
        self.assertEqual(goal.x, 100)
