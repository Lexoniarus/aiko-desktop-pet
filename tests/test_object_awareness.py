"""Real World snapshots do not bypass recognition or remembered positions."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import (
    ObjectAwareness,
    held_type_conflicts_with_memory,
)
from aiko_pet.infrastructure.world_motion import motion_parameters
from aiko_pet.pet.mind.object_attention import ObjectAttention
from aiko_pet.pet.mind.object_decisions import ObjectUseContext
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
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
from tools.pet_test_support import object_test_attention, set_test_pet_values


class ObjectAwarenessTests(unittest.TestCase):
    def test_ground_focus_excludes_neighbours_and_their_cursor_take(self):
        world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        subject, neighbour = [world.place_resting("apple", x, ObjectFootprint(4, 4))
                              for x in (100, 110)]
        awareness, state = ObjectAwareness(), PetState(satiety=100)
        for now in (0, .3):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attention=object_test_attention(100, width=100),
                             blocked=True)
        self.identify_observed(awareness, now=.3)
        record = awareness.record_for_instance(subject.instance_id)
        other = awareness.record_for_instance(neighbour.instance_id)
        assert record is not None and other is not None
        original = awareness.memory.get(other)
        focused = ObjectAttention("object", (0, 0), origin=(100, 0), width=100,
                                   focused_place=True)
        world.take_resting(neighbour.instance_id, expected_revision=0)
        self.assertFalse(awareness.follow_taken(neighbour.instance_id, other, now=.4,
                                              attention=focused, committed=record))
        novel = world.place_resting("apple", 120, ObjectFootprint(4, 4))
        for now in (.6, .9, 1.2):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attention=focused, blocked=True,
                             committed=record)
            self.assertEqual({seen.token for seen in awareness.observations}, {record})
            self.assertEqual(awareness.memory.get(other), original)
            self.assertIsNone(awareness.record_for_instance(novel.instance_id))
            self.assertEqual(len(awareness.memory.snapshot()), 2)
            self.assertEqual(awareness.absences, ())

    def test_hand_focus_defers_unrelated_sightings_and_losses_to_a_fresh_look(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        awareness, state = ObjectAwareness(), PetState(satiety=100)
        subject = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        others = [world.place_resting("apple", x, ObjectFootprint(8, 8))
                  for x in (200, 300, 400, 500)]

        def observe(now, attention, **kwargs):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100, attention=attention, blocked=True, **kwargs)

        right = object_test_attention(100, width=100)
        for now in (0, .3):
            observe(now, right)
        self.identify_observed(awareness, now=.3)
        record = awareness.record_for_instance(subject.instance_id)
        assert record is not None
        records = {awareness.record_for_instance(item.instance_id) for item in others}
        world.collect_resting(subject.instance_id, expected_revision=0)
        for item in others:
            assert item.position is not None
            world.move_resting(item.instance_id, item.position.x + 50,
                               expected_revision=0)
        hand = ObjectAttention("object", (0, .4), origin=(100, 0), width=100)
        for now in (.6, .9, 1.2):
            observe(now, hand, held_pose=(100, 40), committed=record, inspecting=record)
            self.assertEqual({seen.token for seen in awareness.observations}, {record})
            self.assertEqual(awareness.absences, ())
        known = awareness.memory.get(record)
        assert known is not None
        self.assertTrue(known.recognized)
        # Looking away supplies neither new sightings nor empty-place evidence.
        left = object_test_attention(100, width=100, height=100, direction=(-1, 0))
        for now in (1.3, 1.6):
            observe(now, left, held_pose=(100, 40))
            self.assertEqual(awareness.absences, ())
            self.assertEqual({seen.token for seen in awareness.observations}, {record})
        # Returning to the scene starts fresh notice and absence dwell.
        observe(1.7, right, held_pose=(100, 40))
        self.assertEqual(awareness.absences, ())
        self.assertEqual(len(awareness.observations), 1)
        for now in (2, 2.3):
            observe(now, right, held_pose=(100, 40))
        self.assertEqual({item.token for item in awareness.absences}, records)
        self.assertTrue(all(not seen.identity for seen in awareness.observations
                            if seen.token != record))

    def test_current_hand_focus_cannot_witness_a_take_from_an_old_binding(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        right = object_test_attention(100, width=100)
        for now in (0, .3):
            awareness.update(world.snapshot(), PetState(), now=now, x=100, height=0,
                             width=100, attention=right, blocked=True)
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        world.take_resting(item.instance_id, expected_revision=0)
        hand = ObjectAttention("object", (0, 1), origin=(100, 0), width=100)
        self.assertFalse(awareness.follow_taken(item.instance_id, record, now=.4,
                                              attention=hand))
        known = awareness.memory.get(record)
        assert known is not None
        self.assertTrue(known.resting)
        self.assertFalse(awareness.following_cursor)
        awareness.update(world.snapshot(), PetState(), now=.5, x=100, height=0,
                         width=100, attention=hand, blocked=True)
        self.assertIsNone(awareness.record_for_instance(item.instance_id))
        self.assertEqual(awareness.absences, ())

    def test_witnessed_take_commits_custody_before_any_held_frame(self):
        for identified in (False, True):
            with self.subTest(identified=identified):
                world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
                    "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
                ),))
                item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
                awareness = ObjectAwareness()
                state = PetState(satiety=100)
                for now in (0, .3):
                    awareness.update(world.snapshot(), state, now=now, x=100,
                                     height=0, width=100,
                                     attention=object_test_attention(
                                         100, width=100,
                                     ), blocked=True)
                record = awareness.record_for_instance(item.instance_id)
                assert record is not None
                if identified:
                    awareness.memory.observe_find(ObjectObservation(
                        "identified", "apple", "food", 100, 0, True, .3,
                    ), now=.3, record=record, claimed=frozenset(), maximum_distance=25,
                        instance_id=item.instance_id)
                held = world.take_resting(item.instance_id, expected_revision=0)
                self.assertTrue(awareness.follow_taken(
                    item.instance_id, record, now=.4,
                    attention=object_test_attention(100, width=100),
                ))
                known = awareness.memory.get(record)
                assert known is not None
                self.assertFalse(known.resting)
                self.assertEqual(known.observed_at, .4)
                world.move_held(item.instance_id, WorldPosition(300, 0),
                                expected_revision=held.revision)
                moved = world.get(item.instance_id)
                world.release(item.instance_id, expected_revision=moved.revision)
                world.advance_motion(1, motion_parameters())
                awareness.update(world.snapshot(), state, now=.6, x=100, height=0,
                                 width=100,
                                 attention=object_test_attention(
                                     100, width=100,
                                 ), blocked=True)
                known = awareness.known_instance(item.instance_id)
                assert known is not None
                self.assertEqual(known.token, record)
                self.assertEqual(known.identity, "apple" if identified else None)
                self.assertEqual(known.place_status, "remembered")
                self.assertEqual(len(awareness.memory.snapshot()), 1)
                self.assertEqual(awareness.absences, ())

    def test_close_learned_pair_survives_restart_and_repeated_focus_changes(self):
        for kinds, places in (
            (("apple", "cookie"), (100, 110)),
            (("apple", "apple"), (100, 110)),
            (("apple", "cookie"), (100, 100)),
            (("apple", "apple"), (100, 100)),
        ):
            with self.subTest(kinds=kinds, places=places):
                world = WorldState(WorldSurface(1600, 900), tuple(
                    ObjectDefinition(kind, kind, kind,
                                     frozenset((ObjectInteraction.EAT,)))
                    for kind in dict.fromkeys(kinds)
                ))
                previous = ObjectAwareness()
                portions = [world.place_resting(kind, x, ObjectFootprint(8, 8))
                            for kind, x in zip(kinds, places, strict=True)]
                records = []
                for item in portions:
                    # Earlier completed hand/face identification, before saving.
                    assert item.position is not None
                    record = previous.memory.observe_find(ObjectObservation(
                        "identified", item.definition_id, "food", item.position.x,
                        0, True, 0,
                    ), now=0, record=None, claimed=frozenset(), maximum_distance=25,
                        instance_id=item.instance_id)
                    previous.memory.mark_assessed(record)
                    records.append(record)
                awareness = ObjectAwareness(previous.memory.export(now=1))
                state = PetState(satiety=100)
                for step in range(40):
                    focus = records[step % 2] if step % 4 else None
                    awareness.update(world.snapshot(), state, now=step * .3,
                                     x=600, height=0, width=100,
                                     attention=object_test_attention(
                                         600, width=100, direction=(-1, 0),
                                     ),
                                     blocked=True, committed=focus)
                for now in (12, 12.3, 12.6):
                    awareness.update(world.snapshot(), state, now=now, x=600,
                                     height=0, width=100,
                                     attention=object_test_attention(
                                         600, width=100, direction=(-1, 0),
                                     ), blocked=True)
                self.assertEqual(len(awareness.memory.snapshot()), 2)
                for item, record in zip(portions, records, strict=True):
                    self.assertEqual(awareness.record_for_instance(item.instance_id),
                                     record)
                    known = awareness.memory.get(record)
                    assert known is not None
                    self.assertTrue(known.assessed)
                self.assertTrue(all(seen.identity is None
                                    for seen in awareness.observations))

    def test_known_place_and_physical_reference_both_require_current_notice(self):
        world = WorldState(WorldSurface(2000, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        previous = ObjectAwareness()
        record = previous.memory.observe_find(ObjectObservation(
            "identified", "apple", "food", 100, 0, True, 0,
        ), now=0, record=None, claimed=frozenset(), maximum_distance=25,
            instance_id=item.instance_id)
        awareness = ObjectAwareness(previous.memory.export(now=1))
        for now, x, attentive in ((0, 1500, True), (.3, 1500, True),
                                   (.6, 100, False), (.9, 100, False),
                                   (1.2, 500, True)):
            awareness.update(world.snapshot(), PetState(), now=now, x=x, height=0,
                             width=100,
                             attention=object_test_attention(
                                 x, width=100, attentive=attentive, direction=(-1, 0),
                             ), blocked=True)
            self.assertIsNone(awareness.record_for_instance(item.instance_id))
        awareness.update(world.snapshot(), PetState(), now=1.5, x=500, height=0,
                         width=100,
                         attention=object_test_attention(
                             500, width=100, direction=(-1, 0),
                         ), blocked=True)
        self.assertEqual(awareness.record_for_instance(item.instance_id), record)
        world.move_resting(item.instance_id, 800, expected_revision=0)
        awareness.update(world.snapshot(), PetState(), now=1.8, x=1500, height=0,
                         width=100,
                         attention=object_test_attention(
                             1500, width=100, attentive=False,
                         ), blocked=True)
        for now in (2.1, 2.4):
            awareness.update(world.snapshot(), PetState(), now=now, x=800, height=0,
                             width=100,
                             attention=object_test_attention(
                                 800, width=100,
                             ), blocked=True)
        unknown = awareness.known_instance(item.instance_id)
        assert unknown is not None
        self.assertIsNone(unknown.identity)
        old = awareness.memory.get(record)
        assert old is not None
        self.assertEqual(old.x, 100)
        world.collect_resting(item.instance_id, expected_revision=1)
        for now in (2.7, 3, 3.4):
            awareness.update(world.snapshot(), PetState(), now=now, x=800, height=0,
                             width=100,
                             attention=object_test_attention(
                                 800, width=100,
                             ), blocked=True,
                             held_pose=(800, 40), committed=unknown.token,
                             inspecting=unknown.token)
        known = awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertEqual((known.token, known.identity), (unknown.token, "apple"))
        self.assertIsNone(awareness.memory.get(record))

    def test_unknown_replacement_at_learned_place_never_borrows_identity(self):
        world = WorldState(WorldSurface(1600, 900), tuple(
            ObjectDefinition(kind, kind, kind, frozenset((ObjectInteraction.EAT,)))
            for kind in ("apple", "cookie")
        ))
        original = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        previous = ObjectAwareness()
        previous.memory.observe_find(ObjectObservation(
            "identified", "apple", "food", 100, 0, True, 0,
        ), now=0, record=None, claimed=frozenset(), maximum_distance=25,
            instance_id=original.instance_id)
        world.remove(original.instance_id, expected_revision=0)
        replacement = world.place_resting("cookie", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness(previous.memory.export(now=1))
        for now in (0, .3, .6):
            awareness.update(world.snapshot(), PetState(), now=now, x=500, height=0,
                             width=100,
                             attention=object_test_attention(
                                 500, width=100, direction=(-1, 0),
                             ), blocked=True)
        unknown = awareness.known_instance(replacement.instance_id)
        assert unknown is not None
        self.assertIsNone(unknown.identity)
        self.assertIsNone(unknown.instance_id)
        self.assertFalse(unknown.assessed)

    def test_held_guard_checks_actual_type_without_identifying_from_world(self):
        world = WorldState(WorldSurface(1600, 900), (
            ObjectDefinition("apple", "apple", "apple",
                             frozenset((ObjectInteraction.EAT,))),
            ObjectDefinition("cookie", "cookie", "cookie",
                             frozenset((ObjectInteraction.EAT,))),
        ))
        apple = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        known = ObjectKnowledge("memory_1", "apple", "food", 100, 0,
                                False, 1, assessed=True)
        self.assertTrue(held_type_conflicts_with_memory(
            known, apple.instance_id, world.snapshot(),
        ))
        taken = world.collect_resting(apple.instance_id, expected_revision=0)
        self.assertFalse(held_type_conflicts_with_memory(
            known, taken.instance_id, world.snapshot(),
        ))
        world.consume(taken.instance_id, expected_revision=taken.revision)
        cookie = world.place_resting("cookie", 100, ObjectFootprint(8, 8))
        cookie = world.collect_resting(cookie.instance_id, expected_revision=0)
        self.assertTrue(held_type_conflicts_with_memory(
            known, cookie.instance_id, world.snapshot(),
        ))
        unknown = replace(known, identity=None, kind=None, assessed=False)
        self.assertFalse(held_type_conflicts_with_memory(
            unknown, cookie.instance_id, world.snapshot(),
        ))
        self.assertEqual((known.identity, known.assessed), ("apple", True))

    def test_unknown_occupied_place_resumes_curiosity_after_a_tracking_gap(self):
        world = WorldState(WorldSurface(1600, 900), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 200, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for now in (0, .3):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=False)
        record = awareness.record_for_instance(item.instance_id)
        for now in (2, 2.3):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=False, committed=record)
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
                             width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=False)
        record = awareness.record_for_instance(item.instance_id)
        world.remove(item.instance_id, expected_revision=0)
        world.place_resting("apple", 200, ObjectFootprint(8, 8))
        for now in (.4, .7, 1):
            awareness.update(world.snapshot(), state, now=now, x=100, height=0,
                             width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=False, committed=record)
        self.assertEqual(awareness.absences, ())
        self.assertFalse(awareness.checking_absence)
        self.assertTrue(all(item.identity is None
                            for item in awareness.memory.snapshot()))

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
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100, mode="cursor",
                             ), blocked=True,
                             presentation=(item.instance_id,
                                           ItemPresentation("one", 0, 0)))
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        self.assertIsNone(awareness.assess_offer(record, state))
        awareness.update(world.snapshot(), state, now=1.1, x=100,
                         height=0, width=100,
                         attention=object_test_attention(
                             100, width=100, mode="cursor",
                         ), blocked=True,
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
                         height=0, width=100,
                         attention=object_test_attention(
                             100, width=100, mode="cursor",
                         ), blocked=True,
                         presentation=(item.instance_id, ItemPresentation("one", 5, 5)))
        self.assertTrue(awareness.observations[0].presented)
        decision = awareness.assess_offer(record, state)
        assert decision is not None
        self.assertTrue(decision.consume)
        self.assertEqual(len(awareness.memory.snapshot()), 1)
        # Actual loss of attention removes execution evidence and held desire.
        awareness.update(world.snapshot(), state, now=1.5, x=100,
                         height=0, width=100,
                         attention=object_test_attention(
                             100, width=100, attentive=False, mode="cursor",
                         ), blocked=True)
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
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100, mode="cursor",
                             ), blocked=True)

        for stamp in (0, .3, .7):
            observe(stamp)
        self.identify_observed(awareness, now=.7)
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        world.take_resting(item.instance_id, expected_revision=0)
        self.assertTrue(awareness.follow_taken(
            item.instance_id, record, now=.8,
            attention=object_test_attention(100, width=100),
        ))
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
                         height=0, width=100,
                         attention=object_test_attention(
                             100, width=100, attentive=False, mode="cursor",
                         ), blocked=True)
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
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=True)
        neighbour, = awareness.memory.snapshot()
        self.identify_observed(awareness, now=.7)
        target = world.place_resting("apple", 110, ObjectFootprint(8, 8))
        for stamp in (.8, 1.1):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=True)
        record = awareness.record_for_instance(target.instance_id)
        assert record is not None
        self.assertNotEqual(record, neighbour.token)
        world.take_resting(target.instance_id, expected_revision=0)
        self.assertTrue(awareness.follow_taken(
            target.instance_id, record, now=1.1,
            attention=object_test_attention(100, width=100),
        ))
        for stamp in (1.2, 1.6, 2, 2.3):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100,
                             ), blocked=True,
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
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100, mode="cursor",
                             ), blocked=True)
        record = awareness.record_for_instance(item.instance_id)
        assert record is not None
        self.identify_observed(awareness, now=.7)
        awareness.memory.mark_assessed(record)
        world.take_resting(item.instance_id, expected_revision=0)
        self.assertTrue(awareness.follow_taken(
            item.instance_id, record, now=.8,
            attention=object_test_attention(100, width=100),
        ))
        held = world.get(item.instance_id)
        world.move_held(item.instance_id, WorldPosition(1400, 700),
                        expected_revision=held.revision)
        awareness.update(world.snapshot(), state, now=.9, x=100, height=0,
                         width=100,
                         attention=object_test_attention(
                             100, width=100, mode="cursor",
                         ), blocked=True, committed=record)
        known = awareness.known_instance(item.instance_id)
        assert known is not None
        self.assertEqual((known.token, known.identity, known.x),
                         (record, "apple", 1400))
        self.assertTrue(known.assessed)
        awareness.update(world.snapshot(), state, now=1, x=100, height=0,
                         width=100,
                         attention=object_test_attention(
                             100, width=100, attentive=False, mode="cursor",
                         ), blocked=True, committed=record)
        self.assertIsNone(awareness.instance_for_record(record))

    def test_free_movement_observes_forward_changes_without_item_focus(self):
        world = WorldState(WorldSurface(1600, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        target = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        other = world.place_resting("apple", 200, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for stamp in (0, .3, .7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100, mode="moving",
                             ), blocked=True)
        focus = awareness.record_for_instance(target.instance_id)
        old = awareness.known_instance(other.instance_id)
        assert focus is not None and old is not None
        world.move_resting(other.instance_id, 250, expected_revision=0)
        dropped = world.place_resting("apple", 150, ObjectFootprint(8, 8))
        for stamp in (1, 1.3, 1.7):
            awareness.update(world.snapshot(), state, now=stamp, x=100,
                             height=0, width=100,
                             attention=object_test_attention(
                                 100, width=100, mode="moving",
                             ), blocked=True)
        remembered = awareness.memory.get(old.token)
        assert remembered is not None
        self.assertEqual(remembered.place_status, "missing")
        self.assertIn(focus, {item.token for item in awareness.observations})
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
                                     height=0, width=100,
                                     attention=object_test_attention(
                                         100, width=100,
                                     ), blocked=True)
                self.identify_observed(awareness, now=.7)
                old, = awareness.memory.snapshot()
                awareness.memory.mark_assessed(old.token)
                world.move_resting(item.instance_id, 800, expected_revision=0)
                awareness.update(world.snapshot(), state, now=1, x=100, height=0,
                                 width=100,
                                 attention=object_test_attention(
                                     100, width=100, attentive=False,
                                 ), blocked=True)
                if missing_first:
                    awareness.memory.mark_missing(old.token)
                for stamp in (2, 2.3, 2.7):
                    awareness.update(world.snapshot(), state, now=stamp, x=800,
                                     height=0, width=100,
                                     attention=object_test_attention(
                                         800, width=100,
                                     ), blocked=True)
                found = awareness.known_instance(item.instance_id)
                assert found is not None
                self.assertNotEqual(found.token, old.token)
                self.assertFalse(found.assessed)
                # Identification happens only after the newly found portion is
                # actually collected and inspected, not from its ground position.
                world.collect_resting(item.instance_id, expected_revision=1)
                for stamp in (2.8, 3.1, 3.5):
                    awareness.update(world.snapshot(), state, now=stamp, x=800,
                                     height=0, width=100,
                                     attention=object_test_attention(
                                         800, width=100,
                                     ), blocked=True,
                                     held_pose=(800, 40), inspecting=found.token)
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
                             x=0, height=0, width=192,
                             attention=object_test_attention(
                                 0, width=192, attentive=attentive,
                             ),
                             blocked=True)
            self.assertEqual(awareness.observations, ())
        awareness.update(world.snapshot(), PetState(satiety=100), now=1000.3,
                         x=0, height=0, width=192,
                         attention=object_test_attention(
                             0, width=192,
                         ), blocked=True)
        self.assertIsNone(awareness.observations[0].identity)
        self.assertEqual(awareness.memory.snapshot()[0].identity, "apple")
        self.assertTrue(awareness.memory.snapshot()[0].assessed)

    def test_hidden_relocation_does_not_update_subjective_goal(self):
        world = WorldState(WorldSurface(2000, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        awareness = ObjectAwareness()
        state = PetState(satiety=50)
        for now in (0, 0.3, 0.7):
            goal = awareness.update(world.snapshot(), state, now=now, x=0,
                                    height=0, width=192,
                                    attention=object_test_attention(
                                        0, width=192,
                                    ), blocked=False)
        assert goal is not None
        world.move_resting(item.instance_id, 1500, expected_revision=0)
        goal = awareness.update(world.snapshot(), state, now=2, x=0,
                                height=0, width=192,
                                attention=object_test_attention(
                                    0, width=192,
                                ), blocked=False)
        self.assertIsNone(goal)
        self.assertTrue(awareness.checking_absence)
        self.assertEqual(awareness.memory.snapshot()[0].x, 100)
        self.assertEqual(awareness.absences, ())
        awareness.update(world.snapshot(), state, now=2.5, x=0, height=0,
                         width=192,
                         attention=object_test_attention(
                             0, width=192,
                         ), blocked=False)
        self.assertEqual(awareness.absences[0].x, 100)
        self.assertIsNone(awareness.absences[0].identity)
