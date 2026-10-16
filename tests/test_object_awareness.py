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
    def test_recognition_cannot_merge_focus_with_an_unobserved_known_neighbour(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        world.place_resting("apple", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for stamp in (0, .3, .7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)
        neighbour, = awareness.memory.snapshot()
        target = world.place_resting("apple", 110, ObjectFootprint(8, 8))
        for stamp in (.8, 1.1):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)
        record = awareness.record_for_instance(target.instance_id)
        assert record is not None
        self.assertNotEqual(record, neighbour.token)
        awareness.update(world.snapshot(), state, now=1.5, x=100,
                         height=0, width=100, attentive=True, blocked=True,
                         committed=record)
        self.assertEqual(awareness.record_for_instance(target.instance_id), record)
        self.assertIsNotNone(awareness.memory.get(neighbour.token))
        known = awareness.memory.get(record)
        assert known is not None
        self.assertEqual(known.identity, "apple")

    def test_following_a_visible_take_preserves_knowledge_outside_notice_radius(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for stamp in (0, .3, .7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        awareness.memory.mark_assessed(record)
        world.take_resting(item.instance_id, expected_revision=0)
        self.assertTrue(awareness.follow_taken(item.instance_id, record))
        held = world.get(item.instance_id)
        world.move_held(item.instance_id, WorldPosition(1400, 700),
                        expected_revision=held.revision)
        awareness.update(world.snapshot(), state, now=.9, x=100, height=0,
                         width=100, attentive=True, blocked=True, committed=record)
        known = awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertEqual((known.token, known.identity, known.x),
                         (record, "apple", 1400))
        self.assertTrue(known.assessed)
        awareness.update(world.snapshot(), state, now=1, x=100, height=0,
                         width=100, attentive=False, blocked=True, committed=record)
        self.assertIsNone(awareness.instance_for_record(record))

    def test_commitment_filters_other_drops_and_relocations_before_memory(self):
        world = WorldState(WorldSurface(1600, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        target = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        other = world.place_resting("apple", 200, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for stamp in (0, .3, .7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)
        focus = awareness.record_for_instance(target.instance_id)
        old = awareness.known_instance(other.instance_id)
        assert focus is not None and old is not None
        world.move_resting(other.instance_id, 250, expected_revision=0)
        dropped = world.place_resting("apple", 150, ObjectFootprint(8, 8))
        for stamp in (1, 1.3, 1.7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True,
                             committed=focus)
        self.assertEqual(awareness.memory.get(old.token), old)
        self.assertIsNone(awareness.known_instance(dropped.instance_id))
        self.assertEqual({item.token for item in awareness.observations}, {focus})
        for stamp in (2, 2.3, 2.7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)
        self.assertIsNotNone(awareness.known_instance(dropped.instance_id))

    def test_unseen_relocation_is_a_new_find_and_both_discovery_orders_reconcile(self):
        for missing_first in (False, True):
            with self.subTest(missing_first=missing_first):
                world = WorldState(WorldSurface(2000, 600), (ObjectDefinition(
                    "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
                ),))
                item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
                awareness = ObjectAwareness()
                state = PetState(satiety=100)
                for stamp in (0, .3, .7):
                    awareness.update(world.snapshot(), state, now=stamp, x=100,
                                     height=0, width=100, attentive=True, blocked=True)
                old, = awareness.memory.snapshot()
                awareness.memory.mark_assessed(old.token)
                world.move_resting(item.instance_id, 700, expected_revision=0)
                awareness.update(world.snapshot(), state, now=1, x=100, height=0,
                                 width=100, attentive=False, blocked=True)
                if missing_first:
                    awareness.memory.mark_missing(old.token)
                for stamp in (2, 2.3, 2.7):
                    awareness.update(world.snapshot(), state, now=stamp, x=700,
                                     height=0, width=100, attentive=True, blocked=True)
                found = awareness.known_instance(item.instance_id)
                assert found is not None
                self.assertNotEqual(found.token, old.token)
                self.assertFalse(found.assessed)
                if not missing_first:
                    self.assertEqual(found.possible_sources, (old.token,))
                    awareness.memory.mark_missing(old.token)
                self.assertEqual(len(awareness.memory.snapshot()), 1)
                self.assertEqual(awareness.instance_for_record(found.token),
                                 item.instance_id)

    def test_offer_assessment_requires_current_recognition_and_attention(self):
        awareness = ObjectAwareness()
        seen = ObjectObservation("one", "apple", "food", 100, 70, False, 1)
        awareness.memory.update((seen,), now=1)
        state = PetState(satiety=50)
        self.assertIsNone(awareness.assess_offer("one", state))
        self.assertFalse(awareness.memory.snapshot()[0].assessed)
        awareness.observations = (seen,)
        state.sleeping = True
        self.assertIsNone(awareness.assess_offer("one", state))
        self.assertFalse(awareness.memory.snapshot()[0].assessed)
        state.sleeping = False
        decision = awareness.assess_offer("one", state)
        assert decision is not None
        self.assertTrue(decision.consume)
        self.assertTrue(awareness.memory.snapshot()[0].assessed)

    def test_refused_offer_remains_assessed_after_observed_placement(self):
        awareness = ObjectAwareness()
        seen = ObjectObservation("one", "energy_drink", "drink", 100, 70, False, 1)
        awareness.memory.update((seen,), now=1)
        awareness.observations = (seen,)
        state = PetState(energy=100)
        decision = awareness.assess_offer("one", state)
        assert decision is not None
        self.assertFalse(decision.consume)
        awareness.memory.update((ObjectObservation(
            "one", "energy_drink", "drink", 150, 0, True, 2,
        ),), now=2)
        self.assertIsNone(awareness.intentions.choose(
            awareness.memory.snapshot(), state, x=0, now=2,
        ))
        state.energy = 50
        goal = awareness.intentions.choose(
            awareness.memory.snapshot(), state, x=0, now=3,
        )
        assert goal is not None
        self.assertEqual(goal.purpose, "consume")
        self.assertIsNone(awareness.memory.snapshot()[0].disposition)

    def test_restored_knowledge_is_not_current_visibility_or_sensory_evidence(self):
        world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        previous = ObjectAwareness()
        previous.memory.update((ObjectObservation(
            item.instance_id, "apple", "food", 100, 0, True, 500,
        ),), now=500)
        previous.memory.mark_assessed(item.instance_id)
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
        self.assertTrue(awareness.memory.snapshot()[0].assessed)

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
