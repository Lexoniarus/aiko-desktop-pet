"""A witnessed take preserves knowledge independently of current appetite."""

import unittest

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.infrastructure.world_motion import motion_parameters
from aiko_pet.pet.mind.object_attention import ObjectAttention
from aiko_pet.pet.mind.object_decisions import decide_object_use
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


class ObservedAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(WorldSurface(1800, 900), (ObjectDefinition(
            "cookie", "cookie", "cookie", frozenset((ObjectInteraction.EAT,)),
        ),))
        self.item = self.world.place_resting("cookie", 100, ObjectFootprint(8, 8))
        self.awareness = ObjectAwareness()
        self.record = self.awareness.memory.observe_find(
            ObjectObservation("earlier", "cookie", "food", 100, 0, True, 0),
            now=0, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=self.item.instance_id,
        )
        self.awareness.memory.mark_assessed(self.record)
        self.attention = ObjectAttention("cursor", (-1, 0), origin=(300, 0), width=100)

    def test_between_tick_take_preserves_known_wanted_and_unwanted_portions(self):
        for satiety in (50, 100):
            with self.subTest(satiety=satiety):
                self.setUp()
                state = PetState(satiety=satiety)
                self.assertEqual(decide_object_use(
                    self.awareness.memory.get(self.record), state,
                ).consume, satiety == 50)
                # The known item currently has no completed visibility binding.
                self.assertIsNone(self.awareness.record_for_instance(self.item.instance_id))
                held = self.world.take_resting(self.item.instance_id,
                                               expected_revision=0)
                result = self.awareness.witness_take(
                    held.instance_id, position=(100, 0), now=.1,
                    attention=self.attention,
                )
                self.assertEqual(result, self.record)
                self.assertTrue(self.awareness.following_cursor)
                self.world.move_held(held.instance_id, WorldPosition(1400, 700),
                                     expected_revision=held.revision)
                held = self.world.get(held.instance_id)
                self.world.release(held.instance_id, expected_revision=held.revision)
                self.world.advance_motion(20, motion_parameters())
                self.awareness.update(
                    self.world.snapshot(), state, now=.3, x=300, height=0, width=100,
                    attention=self.attention, blocked=True,
                )
                known = self.awareness.known_instance(held.instance_id)
                assert known is not None
                self.assertEqual((known.token, known.identity, known.resting),
                                 (self.record, "cookie", True))
                self.assertTrue(known.assessed)
                self.assertEqual(len(self.awareness.memory.snapshot()), 1)
                self.assertEqual(self.awareness.absences, ())

    def test_an_unseen_new_place_or_other_instance_cannot_use_the_old_reference(self):
        for replacement in (False, True):
            with self.subTest(replacement=replacement):
                self.setUp()
                if replacement:
                    item = self.world.place_resting("cookie", 100,
                                                    ObjectFootprint(8, 8))
                    position = (100, 0)
                else:
                    item = self.world.move_resting(self.item.instance_id, 300,
                                                   expected_revision=0)
                    position = (300, 0)
                self.world.take_resting(item.instance_id,
                                       expected_revision=item.revision)
                self.assertIsNone(self.awareness.witness_take(
                    item.instance_id, position=position, now=.1,
                    attention=self.attention,
                ))
                self.assertFalse(self.awareness.following_cursor)

    def test_another_activity_or_focused_subject_cannot_witness_the_take(self):
        for focused in (False, True):
            with self.subTest(focused=focused):
                self.setUp()
                other = self.world.place_resting("cookie", 110, ObjectFootprint(8, 8))
                other_record = self.awareness.memory.observe_find(
                    ObjectObservation("other", "cookie", "food", 110, 0, True, 0),
                    now=0, record=None, claimed=frozenset((self.record,)),
                    maximum_distance=0, instance_id=other.instance_id,
                )
                attention = (ObjectAttention(
                    "object", (-1.9, 0), origin=(300, 0), width=100, focused_place=True,
                ) if focused else ObjectAttention("unavailable", None))
                committed = other_record if focused else None
                original = self.awareness.memory.snapshot()
                self.world.take_resting(self.item.instance_id, expected_revision=0)
                self.assertIsNone(self.awareness.witness_take(
                    self.item.instance_id, position=(100, 0), now=.1,
                    attention=attention, committed=committed,
                ))
                self.assertEqual(self.awareness.memory.snapshot(), original)
                self.assertFalse(self.awareness.following_cursor)
