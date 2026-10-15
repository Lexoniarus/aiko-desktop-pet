"""Real World snapshots do not bypass recognition or remembered positions."""

import unittest

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectAwarenessTests(unittest.TestCase):
    def test_restored_knowledge_is_not_current_visibility_or_sensory_evidence(self):
        world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        previous = ObjectAwareness()
        previous.memory.update((ObjectObservation(
            item.instance_id, "apple", "food", 100, 0, True, 500,
        ),), now=500)
        previous.memory.mark_examined(item.instance_id)
        awareness = ObjectAwareness(previous.memory.export(now=500))
        self.assertEqual(awareness.observations, ())
        known = awareness.memory.get(item.instance_id)
        assert known is not None
        self.assertEqual(known.identity, "apple")
        for now, attentive in ((0, False), (1000, False), (1000, True)):
            awareness.update(world.snapshot(), PetState(satiety=100), now=now,
                             x=0, height=0, width=192, attentive=attentive,
                             blocked=True)
            self.assertEqual(awareness.observations, ())
        awareness.update(world.snapshot(), PetState(satiety=100), now=1000.3,
                         x=0, height=0, width=192, attentive=True, blocked=True)
        self.assertIsNone(awareness.observations[0].identity)
        self.assertEqual(awareness.memory.snapshot()[0].identity, "apple")
        self.assertTrue(awareness.memory.snapshot()[0].examined)

    def test_hand_inspection_uses_available_observation_instead_of_hidden_truth(self):
        world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.create_held("apple", WorldPosition(100, 100),
                                 ObjectFootprint(8, 8))
        world.accept_handover_on_release(item.instance_id, expected_revision=0)
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        awareness.update(world.snapshot(), state, now=0, x=0, height=0, width=192,
                         attentive=True, blocked=True)
        self.assertEqual(awareness.memory.snapshot(), ())
        for now in (1, 1.3, 1.7):
            awareness.update(world.snapshot(), state, now=now, x=0, height=0,
                             width=192, attentive=True, blocked=True, held_pose=(0, 70))
        self.assertEqual(awareness.memory.snapshot()[0].identity, "apple")

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
