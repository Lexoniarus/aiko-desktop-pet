"""Diagnostic totals do not supply knowledge about hidden World changes."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_status import (
    ObjectStatusSnapshot,
    snapshot_object_status,
)
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectStatusTests(unittest.TestCase):
    def test_counts_portions_separately_from_subjective_place_and_history(self):
        world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        first, second, unknown = [world.place_resting("apple", x, ObjectFootprint(8, 8))
                                  for x in (100, 200, 300)]
        world.create_held("apple", WorldPosition(400, 50), ObjectFootprint(8, 8))
        known = ObjectKnowledge("first", "apple", "food", 100, 0, True, 0,
                                instance_id=first.instance_id)
        missing = replace(known, token="second", place_status="missing",
                          instance_id=second.instance_id, x=400)
        ambiguous = replace(known, token="ambiguous", instance_id=None,
                            possible_sources=("first",))
        memory = (known, missing, ambiguous,
                  replace(known, token="old", place_status="superseded"),
                  ObjectKnowledge(unknown.instance_id, None, None, 300, 0, True, 0))
        before = world.snapshot()
        self.assertEqual(
            snapshot_object_status(before, memory),
            ObjectStatusSnapshot(desktop=3, known=3, assigned=1, missing=1),
        )
        # A hidden move must not be interpreted as an additional missing memory.
        world.move_resting(first.instance_id, 500, expected_revision=first.revision)
        self.assertEqual(snapshot_object_status(world.snapshot(), memory),
                         snapshot_object_status(before, memory))
        self.assertEqual(known.x, 100)
