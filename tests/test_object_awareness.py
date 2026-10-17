"""Real World snapshots do not bypass recognition or remembered positions."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.infrastructure.world_motion import motion_parameters
from aiko_pet.pet.mind.object_decisions import ObjectUseContext
from aiko_pet.pet.mind.object_perception import ItemPresentation, ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.pet_test_support import set_test_pet_values


class ObjectAwarenessTests(unittest.TestCase):
    def test_unknown_occupied_place_resumes_curiosity_after_a_tracking_gap(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 200, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for now in (0, .3):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attentive=True, blocked=False)
        record = awareness.record_for_instance(item.instance_id)
        for now in (2, 2.3):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attentive=True, blocked=False, committed=record)
        self.assertEqual(awareness.record_for_instance(item.instance_id), record)
        self.assertEqual(len(awareness.memory.snapshot()), 1)
        self.assertIsNone(awareness.observations[0].identity)
        self.assertEqual(awareness.absences, ())

    def test_focused_empty_place_waits_for_unnoticed_occupant(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 200, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for now in (0, .3):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attentive=True, blocked=False)
        record = awareness.record_for_instance(item.instance_id)
        world.remove(item.instance_id, expected_revision=0)
        world.place_resting("apple", 200, ObjectFootprint(8, 8))
        for now in (.4, .7, 1):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attentive=True, blocked=False, committed=record)
        self.assertEqual(awareness.absences, ())
        self.assertFalse(awareness.checking_absence)
        self.assertTrue(all(item.identity is None
                            for item in awareness.memory.snapshot()))

    def test_unrelated_places_wait_until_committed_attention_is_released(self):
        world = WorldState(WorldSurface(1600, 900), ())
        awareness = ObjectAwareness()
        awareness.memory.update((ObjectObservation(
            "old", None, None, 100, 0, True, 0,
        ),), now=0)
        for now in (0, .3, .6):
            awareness.update(world.snapshot(), PetState(), now=now, x=100,
                             height=0, width=100, attentive=True, blocked=False,
                             committed="other")
        self.assertEqual(awareness.absences, ())
        for now in (.7, 1, 1.2):
            awareness.update(world.snapshot(), PetState(), now=now, x=100,
                             height=0, width=100, attentive=True, blocked=False)
        self.assertEqual(awareness.absences[0].token, "old")
        awareness.acknowledge_absence("old")
        awareness.update(world.snapshot(), PetState(), now=1.5, x=100,
                         height=0, width=100, attentive=True, blocked=False)
        self.assertEqual(awareness.absences, ())

    @staticmethod
    def identify_observed(awareness, *, now):
        """Seed completed earlier identification for continuity-only fixtures."""
        awareness.memory.update(tuple(replace(seen, identity="apple", kind="food")
                                      for seen in awareness.observations), now=now)

    def test_unknown_offer_can_become_known_and_wanted_during_holding(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.create_held("apple", WorldPosition(100, 80), ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=76)
        for stamp in (0, .3):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True,
                             presentation=(item.instance_id,
                                           ItemPresentation("one", 0, 0)))
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        self.assertIsNone(awareness.assess_offer(record, state))
        awareness.update(world.snapshot(), state, now=1.1, x=100,
                         height=0, width=100, attentive=True, blocked=True,
                         presentation=(item.instance_id, ItemPresentation("one", 0, 0)))
        decision = awareness.assess_offer(record, state)
        assert decision is not None
        self.assertTrue(decision.consume)
        goal = awareness.intentions.goal
        assert goal is not None
        self.assertEqual((goal.token, goal.use_context),
                         (record, ObjectUseContext.CONTINUING_WISH))
        # Moving far away removes fresh recognition, not learned identity.
        world.move_held(item.instance_id, WorldPosition(1400, 700),
                        expected_revision=item.revision)
        awareness.update(world.snapshot(), state, now=1.3, x=100,
                         height=0, width=100, attentive=True, blocked=True,
                         presentation=(item.instance_id, ItemPresentation("one", 5, 5)))
        self.assertTrue(awareness.observations[0].presented)
        decision = awareness.assess_offer(record, state)
        assert decision is not None
        self.assertTrue(decision.consume)
        self.assertEqual(len(awareness.memory.snapshot()), 1)
        # Actual loss of attention removes execution evidence and held desire.
        awareness.update(world.snapshot(), state, now=1.5, x=100,
                         height=0, width=100, attentive=False, blocked=True)
        self.assertIsNone(awareness.assess_offer(record, state))
        self.assertIsNone(awareness.intentions.goal)

    def test_ordinary_observed_take_and_placement_keep_the_same_record(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=100)

        def observe(stamp):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)

        for stamp in (0, .3, .7):
            observe(stamp)
        self.identify_observed(awareness, now=.7)
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        world.take_resting(item.instance_id, expected_revision=0)
        self.assertTrue(awareness.follow_taken(item.instance_id, record))
        held = world.get(item.instance_id)
        world.move_held(item.instance_id, WorldPosition(1400, 700),
                        expected_revision=held.revision)
        observe(.9)
        held = world.get(item.instance_id)
        world.release(item.instance_id, expected_revision=held.revision)
        observe(1.1)
        world.advance_motion(20, motion_parameters())
        observe(1.3)
        known = awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertEqual((known.token, known.identity, known.resting),
                         (record, "apple", True))
        self.assertIsNone(awareness.intentions.goal)
        # Settling releases the special cursor track. A hidden later move is new.
        awareness.update(world.snapshot(), state, now=1.5, x=100,
                         height=0, width=100, attentive=False, blocked=True)
        self.assertIsNone(awareness.instance_for_record(record))

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
        self.identify_observed(awareness, now=.7)
        target = world.place_resting("apple", 110, ObjectFootprint(8, 8))
        for stamp in (.8, 1.1):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True)
        record = awareness.record_for_instance(target.instance_id)
        assert record is not None
        self.assertNotEqual(record, neighbour.token)
        world.take_resting(target.instance_id, expected_revision=0)
        self.assertTrue(awareness.follow_taken(target.instance_id, record))
        for stamp in (1.2, 1.6, 2, 2.3):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100, attentive=True, blocked=True,
                             committed=record, presentation=(
                                 target.instance_id, ItemPresentation("target", 0, 0),
                             ))
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
        self.identify_observed(awareness, now=.7)
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
                self.identify_observed(awareness, now=.7)
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
                # Identification happens only after the newly found portion is
                # actually collected and inspected, not from its ground position.
                world.collect_resting(item.instance_id, expected_revision=1)
                for stamp in (2.8, 3.1, 3.5):
                    awareness.update(world.snapshot(), state, now=stamp, x=700,
                                     height=0, width=100, attentive=True, blocked=True,
                                     held_pose=(700, 40), inspecting=found.token)
                found = awareness.known_instance(item.instance_id)
                assert found is not None
                if not missing_first:
                    self.assertEqual(found.possible_sources, (old.token,))
                    awareness.memory.mark_missing(old.token)
                self.assertEqual(len(awareness.memory.snapshot()), 1)
                self.assertEqual(awareness.instance_for_record(found.token),
                                 item.instance_id)

    def test_offer_assessment_requires_current_recognition_and_attention(self):
        awareness = ObjectAwareness()
        seen = ObjectObservation(
            "one", "apple", "food", 100, 70, False, 1, presented=True,
        )
        awareness.memory.update((seen,), now=1)
        state = PetState(satiety=50)
        self.assertIsNone(awareness.assess_offer("one", state))
        self.assertFalse(awareness.memory.snapshot()[0].assessed)
        awareness.observations = (seen,)
        set_test_pet_values(state, sleeping=True)
        self.assertIsNone(awareness.assess_offer("one", state))
        self.assertFalse(awareness.memory.snapshot()[0].assessed)
        set_test_pet_values(state, sleeping=False)
        decision = awareness.assess_offer("one", state)
        assert decision is not None
        self.assertTrue(decision.consume)
        self.assertTrue(awareness.memory.snapshot()[0].assessed)

    def test_refused_offer_remains_assessed_after_observed_placement(self):
        awareness = ObjectAwareness()
        seen = ObjectObservation(
            "one", "energy_drink", "drink", 100, 70, False, 1, presented=True,
        )
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
        set_test_pet_values(state, energy=50)
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
        for now in (1, 1.3, 1.7, 2, 2.4):
            awareness.update(world.snapshot(), state, now=now, x=0, height=0,
                             width=192, attentive=True, blocked=True, held_pose=(0, 70),
                             inspecting=awareness.record_for_instance(item.instance_id))
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
        self.assertIsNone(goal)
        self.assertTrue(awareness.checking_absence)
        self.assertEqual(awareness.memory.snapshot()[0].x, 100)
        self.assertEqual(awareness.absences, ())
        awareness.update(world.snapshot(), state, now=2.5, x=0, height=0,
                         width=192, attentive=True, blocked=False)
        self.assertEqual(awareness.absences[0].x, 100)
        self.assertIsNone(awareness.absences[0].identity)
