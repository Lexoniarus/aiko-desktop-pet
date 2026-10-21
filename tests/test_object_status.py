"""Diagnostic totals do not supply knowledge about hidden World changes."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.application.object_status import (
    ObjectStatusSnapshot,
    snapshot_object_status,
)
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.pet_test_support import object_test_attention


class ObjectStatusTests(unittest.TestCase):
    def test_live_discovery_reads_tracker_without_identifying_or_observing(self):
        world = WorldState(WorldSurface(1600, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        world.place_resting("apple", 180, ObjectFootprint(8, 8))
        world.place_resting("apple", 1500, ObjectFootprint(8, 8))
        awareness, pet = ObjectAwareness(), PetState()
        runtime = DesktopWorldRuntime.__new__(DesktopWorldRuntime)
        runtime.world, runtime.awareness = world, awareness
        self.assertEqual(runtime.object_status().undiscovered, 2)
        for now in (0, .3, .6, .9):
            awareness.update(world.snapshot(), pet, now=now, x=100, height=0,
                             width=100, blocked=True,
                             attention=object_test_attention(100, width=100))
        before = awareness.memory.snapshot()
        self.assertEqual(len(before), 1)
        self.assertFalse(before[0].recognized)
        status = runtime.object_status()
        self.assertEqual((status.desktop, status.undiscovered,
                          status.unidentified, status.known, status.unresolved),
                         (2, 1, 1, 0, 0))
        self.assertEqual(awareness.memory.snapshot(), before)
        self.assertEqual(runtime.object_status(), status)

    def test_ambiguous_sightings_do_not_become_undiscovered_or_known(self):
        world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        first, second = [world.place_resting("apple", x, ObjectFootprint(8, 8))
                         for x in (100, 200)]
        memory = (ObjectKnowledge("sighting", None, None, 300, 0, True, 0),)
        status = snapshot_object_status(world.snapshot(), memory)
        self.assertEqual((status.undiscovered, status.unresolved, status.known),
                         (0, 2, 0))
        # A conflicting association does not make a single sighting two objects.
        status = snapshot_object_status(world.snapshot(), memory,
            observed_bindings=((first.instance_id, "sighting"),
                               (second.instance_id, "sighting")))
        self.assertEqual((status.undiscovered, status.unresolved), (0, 2))
        # One valid existing tracker binding leaves the second portion undiscovered.
        status = snapshot_object_status(world.snapshot(), memory,
            observed_bindings=((first.instance_id, "sighting"),))
        self.assertEqual((status.undiscovered, status.unidentified, status.unresolved),
                         (1, 1, 0))

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
            ObjectStatusSnapshot(desktop=3, known=3, assigned=1, missing=1,
                                 unidentified=1, unresolved=1),
        )
        # A hidden move must not be interpreted as an additional missing memory.
        world.move_resting(first.instance_id, 500, expected_revision=first.revision)
        self.assertEqual(snapshot_object_status(world.snapshot(), memory),
                         snapshot_object_status(before, memory))
        self.assertEqual(known.x, 100)
