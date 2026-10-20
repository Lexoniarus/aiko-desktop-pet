"""Behavior coordination uses real application owners without a desktop or Tk."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import (
    ObjectAwareness,
    held_type_conflicts_with_memory,
)
from aiko_pet.application.object_behavior import (
    Approach,
    BehaviorFacts,
    GazeTarget,
    Hold,
    ObjectBehaviorCoordinator,
    SearchMotion,
    choose_object_attention,
)
from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.application.object_interaction_state import SearchPosition
from aiko_pet.pet.mind.object_attention import ObjectAttention
from aiko_pet.pet.mind.object_decisions import ObjectUseContext
from aiko_pet.pet.mind.object_intentions import ObjectGoal
from aiko_pet.pet.mind.object_perception import ConsumableKind, ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.pet_test_support import set_test_pet_values


class ObjectBehaviorTests(unittest.TestCase):
    def test_acute_food_search_uses_existing_route_without_inventing_a_loss(self):
        set_test_pet_values(self.state, satiety=0)
        self.awareness.memory.restore_snapshot(())
        self.interaction.start_food_search()
        self.assertTrue(self.interaction.search_ready)
        self.assertEqual(self.awareness.memory.snapshot(), ())
        self.assertEqual(self.cues, [])
        first = self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 50),
        )
        self.assertEqual(first, SearchMotion(750, .5))
        self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 750),
        )
        self.assertFalse(self.interaction.search_active)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.awareness.memory.snapshot(), ())
        self.assertEqual(self.cues, [])

    def test_acute_food_search_uses_normal_investigation_of_unknown_find(self):
        set_test_pet_values(self.state, satiety=0)
        self.awareness.memory.restore_snapshot(())
        self.interaction.start_food_search()
        observation = ObjectObservation("candidate", None, None, 240, 0, True, 0)
        self.awareness.memory.update((observation,), now=0)
        self.awareness.observations = (observation,)
        motion = self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 50),
        )
        self.assertEqual(motion, Hold())
        self.assertEqual(self.interaction.phase, "approach")
        self.assertTrue(self.interaction.search_active)

    def test_endpoint_waits_for_local_evidence_and_collects_another_loss(self):
        subject = self.awareness.memory.get("stock")
        assert subject is not None
        self.awareness.memory.restore_snapshot((replace(subject, instance_id="old"),))
        edge = self.world.place_resting("apple", 740, ObjectFootprint(8, 8))
        edge_record = self.awareness.memory.observe_find(ObjectObservation(
            "edge", "apple", "food", 740, 0, True, 0,
        ), now=0, record="edge", claimed=frozenset(), maximum_distance=0,
            instance_id=edge.instance_id)
        self.start_search()
        self.acknowledge()
        self.observe(x=50)
        self.behavior.advance_search(blocked=False,
                                     position=SearchPosition(50, 750, 50))
        # This learned place becomes empty only after the pass has begun.
        self.world.move_resting(edge.instance_id, 400, expected_revision=0)
        self.now = .3
        observation = self.observe(x=750)
        motion = self.behavior.advance(observation.goal, blocked=observation.blocked,
                                       search_position=SearchPosition(50, 750, 750))
        self.assertIsInstance(motion, Hold)
        self.assertTrue(self.awareness.checking_absence)
        self.assertEqual(self.interaction.phase, "search")
        self.now = .9
        observation = self.observe(x=750)
        self.behavior.advance(observation.goal, blocked=observation.blocked,
                              search_position=SearchPosition(50, 750, 750))
        self.finish_orientation(x=750)
        self.assertEqual(self.awareness.absences, ())
        self.assertEqual(self.interaction.phase, "search")
        self.interaction.update()
        self.assertEqual((self.cues[-1].event, self.cues[-1].record_id),
                         ("object_place_missing", edge_record))
        self.acknowledge()
        self.behavior.advance_search(blocked=False,
                                     position=SearchPosition(50, 750, 750))
        self.assertEqual(self.interaction.phase, "missing")
        self.assertEqual([cue.event for cue in self.cues].count("object_search"), 1)

    def test_multiple_losses_share_one_pass_and_verified_finds_do_not_reset_it(self):
        subject = self.awareness.memory.get("stock")
        assert subject is not None
        self.awareness.memory.restore_snapshot((
            replace(subject, instance_id="portion_1"),
        ))
        self.awareness.memory.update((ObjectObservation(
            "second", "apple", "food", 200, 0, True, 0,
        ),), now=0)
        self.awareness.memory.restore_snapshot(tuple(
            replace(item, instance_id="portion_2") if item.token == "second" else item
            for item in self.awareness.memory.snapshot()
        ))
        self.observe()
        self.now = .6
        self.observe()
        self.finish_orientation()
        self.assertEqual(self.awareness.absences, ())
        self.assertFalse(self.interaction.notice_absence(replace(
            subject, token="reconciled_record", instance_id="portion_1",
        )))
        self.acknowledge()
        self.acknowledge()
        self.acknowledge()
        self.interaction.search_destination(SearchPosition(50, 750, 50))
        goal = self.alternative(observed=True)
        self.awareness.memory.restore_snapshot(tuple(
            replace(item, instance_id="portion_1") if item.token == goal.token else item
            for item in self.awareness.memory.snapshot()
        ))
        self.behavior.advance_search(blocked=False)
        self.assertEqual(self.interaction.phase, "found")
        self.acknowledge()
        self.assertEqual(self.interaction.phase, "search")
        self.assertEqual(self.interaction.memory_id, "second")
        self.assertEqual(self.interaction.search_progress, .5)
        self.assertEqual([cue.event for cue in self.cues].count("object_search"), 1)
        self.interaction.interrupt(lambda: None)
        self.assertFalse(self.interaction.search_active)
        self.assertEqual(self.interaction.search_progress, 0)

    def test_each_loss_waits_for_its_own_receipt_before_shared_search(self):
        first = self.awareness.memory.get("stock")
        assert first is not None
        losses = (first, replace(first, token="drink", identity="energy_drink",
                                 kind="drink"), replace(first, token="rice",
                                                       identity="onigiri"))
        for known in losses:
            self.assertTrue(self.interaction.notice_absence(known))
        self.assertEqual(len(self.cues), 1)
        first_key = self.cues[-1].key
        self.acknowledge()
        second_key = self.cues[-1].key
        self.assertNotEqual(first_key, second_key)
        self.interaction.receive_feedback(FeedbackReceipt(first_key, True))
        self.interaction.update()
        self.assertEqual(len(self.cues), 2)
        self.acknowledge()
        self.assertFalse(self.interaction.search_ready)
        self.acknowledge()
        self.assertEqual(
            [(cue.record_id, cue.identity) for cue in self.cues
             if cue.event == "object_place_missing"],
            [(known.token, known.identity) for known in losses],
        )
        self.assertEqual(self.cues[-1].event, "object_search")
        self.acknowledge()
        self.assertTrue(self.interaction.search_ready)

    def test_new_loss_during_patrol_pauses_for_bubble_and_preserves_route(self):
        self.start_search()
        self.interaction.search_destination(SearchPosition(50, 750, 50))
        self.assertEqual(self.interaction.search_progress, .5)
        first = self.awareness.memory.get("stock")
        assert first is not None
        another = replace(first, token="another", identity="energy_drink",
                          kind="drink")
        self.assertTrue(self.interaction.notice_absence(another))
        self.assertFalse(self.interaction.notice_absence(another))
        self.assertFalse(self.interaction.search_ready)
        self.assertEqual(self.behavior.advance_search(blocked=False), Hold())
        self.interaction.update()
        cue = self.cues[-1]
        self.assertEqual((cue.event, cue.record_id, cue.identity),
                         ("object_place_missing", "another", "energy_drink"))
        self.assertFalse(self.interaction.search_ready)
        self.acknowledge()
        self.assertTrue(self.interaction.search_ready)
        self.assertEqual(self.interaction.memory_id, "stock")
        self.assertEqual(self.interaction.search_progress, .5)
        self.assertEqual([cue.event for cue in self.cues].count("object_search"), 1)

    def test_first_identified_same_type_portion_ends_subjective_search(self):
        subject = self.awareness.memory.get("stock")
        assert subject is not None
        self.awareness.memory.restore_snapshot((replace(
            subject, instance_id="object_1",
        ),))
        self.start_search()
        other = self.alternative(observed=True)
        self.awareness.memory.restore_snapshot(tuple(
            replace(item, instance_id="object_2") if item.token == other.token else item
            for item in self.awareness.memory.snapshot()
        ))
        self.assertIsInstance(self.behavior.advance(
            other, blocked=False, search_position=SearchPosition(50, 750, 100),
        ), Hold)
        self.assertEqual(self.interaction.memory_id, other.token)
        self.assertEqual(self.cues[-1].event, "object_found")
        self.assertIsNone(self.awareness.memory.get("stock"))
        found = self.awareness.memory.get(other.token)
        assert found is not None
        self.assertEqual(found.instance_id, "object_2")
        # Repeating an already-used fact cannot resolve another subject.
        self.assertFalse(self.interaction.found(other.token))
        self.assertEqual(self.interaction.phase, "found")

    def test_verified_physical_reunion_survives_old_memory_record_reconciliation(self):
        subject = self.awareness.memory.get("stock")
        assert subject is not None
        self.awareness.memory.restore_snapshot((replace(
            subject, instance_id="object_1",
        ),))
        self.start_search()
        goal = self.alternative(observed=True)
        # Hand/face recognition has reconciled the old record into the active
        # finding, which still refers to the actually searched physical portion.
        self.awareness.memory.restore_snapshot(tuple(
            replace(item, instance_id="object_1")
            for item in self.awareness.memory.snapshot() if item.token == goal.token
        ))
        self.assertEqual(self.behavior.advance(goal, blocked=False), Hold())
        self.assertEqual(self.interaction.phase, "found")
        self.assertEqual(self.cues[-1].event, "object_found")

    def test_remembered_but_unseen_same_kind_stock_cannot_end_search(self):
        self.start_search()
        self.alternative(observed=False)
        self.assertIsInstance(self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 100),
        ), SearchMotion)
        self.assertEqual(self.interaction.phase, "search")
        self.assertIsNotNone(self.awareness.memory.get("stock"))

    def setUp(self):
        self.state = PetState(satiety=50, energy=100)
        self.world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        self.awareness = ObjectAwareness()
        self.awareness.memory.update((ObjectObservation(
            "stock", "apple", "food", 100, 0, True, 0,
        ),), now=0)
        self.awareness.memory.mark_assessed("stock")
        self.now = 0
        self.cues, self.actions, self.completed = [], [], []
        self.synchronous_feedback = False

        def feedback(cue):
            self.cues.append(cue)
            if self.synchronous_feedback:
                self.interaction.receive_feedback(FeedbackReceipt(cue.key, True))

        def completed(token, consumed):
            self.completed.append((token, consumed))
            self.awareness.intentions.complete(token, self.now, consumed=consumed)

        def play(clip):
            self.actions.append(clip)
            return len(self.actions)

        self.interaction = ObjectInteractionCoordinator(
            self.world, play=play, stop=lambda: None, select_item=lambda _item: None,
            consume=lambda _key, _token, _record, _origin: False,
            resolve_instance=self.awareness.instance_for_record,
            record_for_instance=self.awareness.record_for_instance,
            can_acquire=lambda _token: False, ground_x=lambda _token: 100,
            hand_type_conflicts=lambda record, instance: (
                held_type_conflicts_with_memory(
                    self.awareness.memory.get(record), instance,
                    self.world.snapshot(),
                )
            ),
            completed=completed, memory=self.awareness.memory,
            decide=lambda token, context: self.behavior.decide(token, context),
            feedback=feedback, cancel_feedback=lambda: None, now=lambda: self.now,
            inspection_seconds=1,
        )
        self.behavior = ObjectBehaviorCoordinator(
            self.state, self.awareness, self.interaction, self.world,
        )

    def acknowledge(self):
        self.interaction.receive_feedback(FeedbackReceipt(self.cues[-1].key, True))
        self.interaction.update()

    def start_search(self, *, identified=True):
        if not identified:
            self.awareness.memory.restore_snapshot(())
            self.awareness.memory.update((ObjectObservation(
                "stock", None, None, 100, 0, True, 0,
            ),), now=0)
        self.interaction.begin_goal(ObjectGoal(
            "stock", "apple" if identified else None,
            "food" if identified else None, 100, 0, 0, "investigate",
        ))
        self.acknowledge()
        self.acknowledge()
        self.interaction.start_search()
        self.assertEqual(self.interaction.phase, "search")
        self.acknowledge()

    def alternative(self, *, kind: ConsumableKind = "food", observed=False):
        identity = "apple" if kind == "food" else "energy_drink"
        self.awareness.memory.update((ObjectObservation(
            "alternative", identity, kind, 240, 0, True, 0,
        ),), now=0)
        if observed:
            self.awareness.observations = (ObjectObservation(
                "alternative", identity, kind, 240, 0, True, self.now,
            ),)
        return ObjectGoal("alternative", identity, kind, 240, 0, 0, "investigate")

    def observe(self, *, facts=BehaviorFacts(), x=100, width=100):
        self.interaction.update()
        return self.behavior.observe(
            self.world.snapshot(),
            now=self.now,
            x=x,
            width=width,
            presentation=None,
            facts=facts,
            attention=replace(choose_object_attention(
                self.interaction.phase, sleeping=self.state.sleeping,
                game_open=facts.game_open, walking=0,
                orientation_side=self.behavior.orientation_side,
                cursor=(-1 if x > 100 else 1, 0),
                target=((known.x - x) / width, (known.height - 60) / width)
                if (record := self.interaction.focus_record) is not None
                and (known := self.awareness.memory.get(record)) is not None else None,
            ), origin=(x, 60), width=width),
        )

    def finish_orientation(self, *, facts=BehaviorFacts(), x=100, width=100):
        for _ in range(20):
            self.now += .2
            observation = self.observe(facts=facts, x=x, width=width)
            if self.behavior.orientation_side is None:
                return observation
        self.fail("Deliberate orientation did not complete")

    def observed_stock(self):
        self.awareness.memory.restore_snapshot(())
        item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.observe()
        self.now = .3
        observation = self.observe()
        assert observation.goal is not None
        goal = observation.goal
        self.awareness.memory.observe_find(ObjectObservation(
            goal.token, "apple", "food", 100, 0, True, self.now,
        ), now=self.now, record=goal.token, claimed=frozenset(),
            maximum_distance=25, instance_id=item.instance_id)
        return item, replace(goal, identity="apple", kind="food")

    def test_fresh_place_check_keeps_its_look_before_turning_to_a_new_find(self):
        subject = self.awareness.memory.get("stock")
        assert subject is not None
        self.awareness.memory.restore_snapshot((replace(subject, x=400),))
        self.world.place_resting("apple", 40, ObjectFootprint(8, 8))
        attention = ObjectAttention("survey", (1, 0), origin=(100, 60), width=100)
        for stamp in (0, .3):
            observation = self.behavior.observe(
                self.world.snapshot(), now=stamp, x=100, width=100,
                presentation=None, facts=BehaviorFacts(), attention=attention,
            )
            self.assertIsNone(observation.goal)
        # Model the native adapter using the returned look on the next tick.
        self.assertEqual(observation.gaze, GazeTarget(0, 60))
        observation = self.finish_orientation()
        self.assertTrue(observation.absence_noticed)
        self.assertEqual(self.interaction.phase, "notice_absence")
        self.assertNotIn("object_notice", [cue.event for cue in self.cues])

    def test_place_check_precedes_a_continuing_consumption_wish(self):
        stock = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.awareness.memory.restore_snapshot(tuple(
            replace(known, instance_id=stock.instance_id)
            for known in self.awareness.memory.snapshot()
        ))
        self.world.remove(stock.instance_id, expected_revision=0)
        item = self.world.place_resting("apple", 180, ObjectFootprint(8, 8))
        record = self.awareness.memory.observe_find(ObjectObservation(
            "wish", "apple", "food", 180, 0, True, 0, True,
        ), now=0, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=item.instance_id)
        wish = self.awareness.memory.get(record)
        assert wish is not None
        self.awareness.intentions.assess_offer(wish, self.state)
        for stamp in (0, .3):
            self.now = stamp
            observation = self.observe()
            self.assertIsNone(observation.goal)
            self.assertEqual(self.behavior.advance(
                observation.goal, blocked=observation.blocked,
            ), Hold())
            self.assertFalse(self.interaction.active)
        self.now = .6
        self.assertTrue(self.finish_orientation().absence_noticed)
        self.assertEqual(self.interaction.memory_id, "stock")
        self.acknowledge()
        self.assertTrue(self.interaction.search_active)
        self.assertFalse(any(cue.record_id == record for cue in self.cues))

    def test_replacement_waits_for_both_missing_bubbles_before_investigation(self):
        self.awareness.memory.restore_snapshot(())
        records = []
        for old_x, new_x in ((100, 600), (300, 700)):
            item = self.world.place_resting("apple", old_x, ObjectFootprint(8, 8))
            record = self.awareness.memory.observe_find(ObjectObservation(
                "earlier", "apple", "food", old_x, 0, True, 0,
            ), now=0, record=None, claimed=frozenset(), maximum_distance=0,
                instance_id=item.instance_id)
            self.awareness.memory.mark_assessed(record)
            records.append(record)
            self.world.move_resting(item.instance_id, new_x, expected_revision=0)
        candidate = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.behavior.request_orientation()
        for stamp in (0, .3, .6):
            self.now = stamp
            observation = self.observe()
        observation = self.finish_orientation()
        self.assertTrue(observation.absence_noticed)
        self.assertEqual({item.token for item in self.awareness.memory.snapshot()
                          if item.place_status == "missing"}, set(records))
        for record in records:
            self.assertEqual((self.cues[-1].event, self.cues[-1].record_id),
                             ("object_place_missing", record))
            self.assertEqual(self.behavior.advance(None, blocked=True), Hold())
            self.acknowledge()
        self.assertEqual(self.cues[-1].event, "object_search")
        self.assertEqual(self.behavior.advance_search(blocked=False), Hold())
        self.acknowledge()
        self.assertTrue(self.interaction.search_active)
        for _ in range(6):
            self.now += .2
            observation = self.observe()
            self.behavior.advance(observation.goal, blocked=observation.blocked,
                                  search_position=SearchPosition(50, 750, 100))
            if self.interaction.phase == "approach":
                break
        record = self.interaction.memory_id
        assert record is not None
        self.assertEqual(self.awareness.instance_for_record(record),
                         candidate.instance_id)
        self.assertEqual(self.interaction.phase, "approach")
        self.assertTrue(self.interaction.search_active)
        self.assertEqual(self.cues[-1].event, "object_approach")
        self.assertNotIn("object_notice", [cue.event for cue in self.cues])
        known = self.awareness.memory.get(record)
        assert known is not None
        self.assertFalse(known.recognized)

    def test_close_unknown_pair_releases_orphan_and_selects_observed_portion(self):
        self.awareness.memory.restore_snapshot(())
        items = [self.world.place_resting("apple", x, ObjectFootprint(8, 8))
                 for x in (100, 120)]
        for stamp in (0, .3, .6):
            self.now = stamp
            observation = self.observe()
            self.behavior.advance(observation.goal, blocked=observation.blocked)
            if self.cues:
                self.acknowledge()
        old = self.interaction.memory_id
        assert old is not None
        for stamp in (2, 2.3, 2.6, 2.9, 3.2, 3.5):
            self.now = stamp
            observation = self.observe()
            self.behavior.advance(observation.goal, blocked=observation.blocked)
            if self.cues:
                self.acknowledge()
        self.assertIsNone(self.awareness.memory.get(old))
        self.assertNotEqual(self.interaction.memory_id, old)
        current = self.interaction.memory_id
        assert current is not None
        self.assertIn(self.awareness.instance_for_record(current),
                      {item.instance_id for item in items})
        self.assertNotIn("object_search", [cue.event for cue in self.cues])
        self.assertTrue(all(not item.recognized
                            for item in self.awareness.memory.snapshot()))

    def test_pending_target_sighting_is_not_an_unresolved_completed_observation(self):
        item, goal = self.observed_stock()
        self.behavior.advance(goal, blocked=False)
        self.acknowledge()
        self.now = 2
        observation = self.observe()
        self.assertFalse(observation.absence_noticed)
        self.assertEqual(self.interaction.memory_id, goal.token)
        self.assertEqual(self.awareness.target_evidence(goal.token, radius=25),
                         "unseen")
        self.now = 2.3
        self.observe()
        self.assertEqual(self.awareness.instance_for_record(goal.token),
                         item.instance_id)

    def test_absence_precedes_discovery_and_only_acknowledges_accepted_notice(self):
        self.world.place_resting("apple", 180, ObjectFootprint(8, 8))
        self.observe()
        self.now = .5
        waiting = self.finish_orientation(facts=BehaviorFacts(user_action_pending=True))
        self.assertFalse(waiting.absence_noticed)
        self.assertFalse(waiting.observe_offer)
        self.assertEqual([item.token for item in self.awareness.absences], ["stock"])
        self.assertFalse(self.interaction.active)
        noticed = self.observe()
        self.assertTrue(noticed.absence_noticed)
        self.assertEqual(noticed.gaze, GazeTarget(100, 0))
        self.assertFalse(noticed.observe_offer)
        self.assertEqual(self.awareness.absences, ())
        self.assertEqual(self.cues[-1].event, "object_place_missing")
        self.assertEqual(self.interaction.memory_id, "stock")

    def test_busy_episode_keeps_unaccepted_absence_pending(self):
        self.observe()
        self.now = .5
        self.finish_orientation(facts=BehaviorFacts(user_action_pending=True))
        self.awareness.memory.update((ObjectObservation(
            "alternative", "apple", "food", 700, 0, True, self.now,
        ),), now=self.now)
        self.interaction.begin_goal(ObjectGoal(
            "alternative", "apple", "food", 700, 0, 0,
        ))
        observation = self.observe()
        self.assertFalse(observation.absence_noticed)
        self.assertFalse(observation.observe_offer)
        self.assertEqual([item.token for item in self.awareness.absences], ["stock"])
        self.assertEqual(observation.gaze, GazeTarget(700, 0))
        self.assertEqual(self.interaction.memory_id, "alternative")

    def test_host_blocking_respects_existing_commitment(self):
        unavailable = self.behavior.observe(
            self.world.snapshot(), now=self.now, x=100, width=100,
            presentation=None, facts=BehaviorFacts(),
            attention=ObjectAttention("unavailable", None, origin=(100, 60), width=100),
        )
        self.assertTrue(unavailable.blocked)
        self.assertIsNone(unavailable.goal)
        for facts in (BehaviorFacts(carrying=True),
                      BehaviorFacts(character_action_busy=True),
                      BehaviorFacts(game_open=True), BehaviorFacts(playback_busy=True)):
            with self.subTest(facts=facts):
                self.assertTrue(self.observe(facts=facts).blocked)
        self.interaction.begin_goal(ObjectGoal("stock", "apple", "food", 100, 0, 0))
        self.assertFalse(self.observe(facts=BehaviorFacts(
            carrying=True, character_action_busy=True,
        )).blocked)
        self.assertTrue(self.observe(facts=BehaviorFacts(game_open=True)).blocked)
        set_test_pet_values(self.state, sleeping=True)
        self.assertTrue(self.observe().blocked)

    def test_blocked_observation_uses_only_current_attention_without_episode(self):
        self.awareness.memory.restore_snapshot(())
        hidden = self.world.place_resting("apple", 10, ObjectFootprint(8, 8))
        visible = self.world.place_resting("apple", 220, ObjectFootprint(8, 8))
        attention = ObjectAttention("survey", (1, 0), origin=(100, 60), width=100)
        for stamp in (0, .3):
            observation = self.behavior.observe(
                self.world.snapshot(), now=stamp, x=100, width=100,
                presentation=None, facts=BehaviorFacts(character_action_busy=True),
                attention=attention,
            )
        self.assertIsNone(observation.goal)
        self.assertEqual(observation.gaze, GazeTarget(220, 0))
        self.assertIsNone(self.awareness.record_for_instance(hidden.instance_id))
        self.assertIsNotNone(self.awareness.record_for_instance(visible.instance_id))
        self.assertIsInstance(self.behavior.advance(None, blocked=True), Hold)
        self.assertFalse(self.interaction.active)

    def test_passive_held_wish_waits_without_creating_an_episode(self):
        self.awareness.memory.update((ObjectObservation(
            "stock", "apple", "food", 100, 40, False, 0,
        ),), now=0)
        goal = ObjectGoal("stock", "apple", "food", 100, 40, 0)
        self.assertIsInstance(self.behavior.advance(goal, blocked=False), Hold)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.cues, [])

    def test_notice_requires_feedback_and_approach_requires_native_arrival(self):
        goal = ObjectGoal("stock", "apple", "food", 100, 0, 0)
        self.assertIsInstance(self.behavior.advance(goal, blocked=False), Hold)
        self.assertEqual(self.interaction.phase, "notice")
        self.acknowledge()
        self.assertEqual(self.behavior.advance(goal, blocked=False), Approach(goal))
        self.assertEqual(self.actions, [])
        self.assertEqual(self.world.snapshot().objects, ())
        self.assertEqual(self.interaction.phase, "approach")

    def test_synchronous_reunion_finishes_without_forcing_another_pickup(self):
        self.start_search()
        goal = self.alternative(observed=True)
        self.synchronous_feedback = True
        self.assertEqual(self.behavior.advance(goal, blocked=False), Hold())
        self.assertEqual(self.interaction.phase, "idle")
        self.assertEqual(self.actions, [])

    def test_return_waiting_holds_once_even_when_return_cue_is_synchronous(self):
        item, goal = self.observed_stock()
        self.behavior.advance(goal, blocked=False)
        self.acknowledge()
        held = self.world.take_resting(item.instance_id, expected_revision=0)
        self.assertTrue(self.interaction.target_taken(goal.token))
        episode = self.interaction.feedback_key.interaction_id
        self.acknowledge()
        self.world.return_user_held(
            item.instance_id, 100, expected_revision=held.revision,
        )
        self.synchronous_feedback = True
        self.assertIsInstance(self.behavior.advance(goal, blocked=True), Hold)
        self.assertEqual(self.interaction.phase, "approach")
        self.assertEqual(self.interaction.feedback_key.interaction_id, episode)
        self.assertEqual(self.behavior.advance(goal, blocked=False), Approach(goal))
        self.assertEqual(self.actions, [])

    def test_lost_return_binding_announces_loss_before_search(self):
        goal = ObjectGoal("stock", "apple", "food", 100, 0, 0)
        self.behavior.advance(goal, blocked=False)
        self.assertTrue(self.interaction.target_taken(goal.token))
        self.assertIsInstance(self.behavior.advance(goal, blocked=True), Hold)
        self.assertEqual(self.interaction.phase, "notice_absence")
        self.acknowledge()
        self.assertEqual(self.interaction.phase, "search")
        self.acknowledge()
        self.assertIsInstance(self.behavior.advance(
            None, blocked=False, search_position=SearchPosition(50, 750, 100),
        ), SearchMotion)

    def test_unreachable_approach_cancels_shared_intention_without_acquiring(self):
        goal = self.awareness.intentions.choose(
            self.awareness.memory.snapshot(), self.state, x=100, now=0,
        )
        assert goal is not None
        self.behavior.advance(goal, blocked=False)
        self.behavior.unreachable(now=self.now)
        self.assertIsNone(self.awareness.intentions.goal)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.completed, [("stock", False)])
        self.assertEqual(self.actions, [])

    def test_snack_preview_does_not_replace_busy_dialogue_or_wake_sleep(self):
        item, _goal = self.observed_stock()
        self.awareness.observations = tuple(
            replace(seen, presented=True) for seen in self.awareness.observations
        )
        self.assertIsNotNone(self.behavior.assess_offer(
            item.instance_id, facts=BehaviorFacts(),
        ))
        for facts in (BehaviorFacts(character_action_busy=True),
                      BehaviorFacts(game_open=True), BehaviorFacts(playback_busy=True)):
            with self.subTest(facts=facts):
                self.assertIsNone(self.behavior.assess_offer(
                    item.instance_id, facts=facts,
                ))
        set_test_pet_values(self.state, sleeping=True)
        self.assertIsNone(self.behavior.assess_offer(
            item.instance_id, facts=BehaviorFacts(),
        ))
        self.assertEqual(self.cues, [])

    def test_stock_changes_preserve_current_orientation_and_object_goal(self):
        self.behavior.request_orientation()
        orientation = self.behavior._orientation
        self.behavior.refresh_after_placement()
        self.assertIs(self.behavior._orientation, orientation)
        _item, goal = self.observed_stock()
        self.behavior.advance(goal, blocked=False)
        phase = self.interaction.phase
        intention = self.awareness.intentions.goal
        self.behavior.refresh_after_placement()
        self.assertEqual(self.interaction.phase, phase)
        self.assertEqual(self.awareness.intentions.goal, intention)

    def test_native_reach_alone_cannot_authorize_an_unseen_or_stale_offer(self):
        item, goal = self.observed_stock()

        def allowed(*, reachable=True, ready=True,
                    now=.3, facts=BehaviorFacts()):
            return self.behavior.can_acquire(
                item.instance_id, object_state=ObjectState.USER_HELD,
                reachable=reachable, offer_ready=ready,
                now=now, facts=facts,
            )

        self.assertTrue(allowed())
        self.assertFalse(allowed(reachable=False))
        self.assertFalse(allowed(ready=False))
        self.assertFalse(allowed(now=.8))
        self.assertFalse(allowed(facts=BehaviorFacts(playback_busy=True)))
        self.assertFalse(allowed(facts=BehaviorFacts(game_open=True)))
        self.assertFalse(allowed(facts=BehaviorFacts(character_action_busy=True)))
        set_test_pet_values(self.state, satiety=100)
        self.assertFalse(allowed())
        set_test_pet_values(self.state, satiety=50)
        self.awareness.observations = ()
        self.assertFalse(allowed())
        self.assertEqual(self.actions, [])
        self.assertEqual(self.world.get(item.instance_id).state, ObjectState.RESTING)
        self.assertEqual(
            goal.token, self.awareness.record_for_instance(item.instance_id),
        )

    def test_unpresented_unknown_cursor_portion_can_be_received_for_inspection(self):
        item, goal = self.observed_stock()
        known = self.awareness.memory.get(goal.token)
        assert known is not None
        self.awareness.memory.restore_snapshot((
            replace(known, identity=None, kind=None, assessed=False),
        ))

        def allowed(**options):
            return self.behavior.can_acquire(
                item.instance_id, object_state=ObjectState.USER_HELD,
                reachable=options.get("reachable", True),
                offer_ready=False, now=options.get("now", self.now),
                facts=options.get("facts", BehaviorFacts()),
            )
        self.assertTrue(allowed())
        self.assertFalse(allowed(reachable=False))
        self.assertFalse(allowed(now=self.now + .6))
        self.assertFalse(allowed(facts=BehaviorFacts(game_open=True)))
        self.assertFalse(allowed(facts=BehaviorFacts(playback_busy=True)))
        self.assertFalse(allowed(facts=BehaviorFacts(character_action_busy=True)))
        self.awareness.observations = ()
        self.assertFalse(allowed())
        latest = self.awareness.memory.get(goal.token)
        assert latest is not None
        self.assertIsNone(latest.identity)

    def test_unbound_recall_waits_for_confirmed_absence_before_search(self):
        self.behavior.request_orientation()
        for stamp in (0, .3):
            self.now = stamp
            observation = self.observe()
            self.assertFalse(observation.absence_noticed)
            self.assertEqual(self.behavior.advance(
                observation.goal, blocked=observation.blocked,
            ), Hold())
            self.assertEqual(self.interaction.phase, "idle")
            self.assertNotIn("object_search", [cue.event for cue in self.cues])
        noticed = self.finish_orientation()
        self.assertTrue(noticed.absence_noticed)
        self.assertEqual(self.interaction.phase, "notice_absence")
        self.assertEqual(self.cues[-1].event, "object_place_missing")
        known = self.awareness.memory.get("stock")
        assert known is not None
        self.assertEqual(known.place_status, "missing")
        self.acknowledge()
        self.assertEqual(self.interaction.phase, "search")
        self.assertEqual(self.cues[-1].event, "object_search")
        self.acknowledge()
        self.now = 1
        self.assertIsInstance(
            self.behavior.advance_search(
                blocked=False, position=SearchPosition(50, 750, 100),
            ), SearchMotion,
        )
        self.assertEqual([cue.event for cue in self.cues].count("object_search"), 1)

    def test_inactive_wish_cancels_abandoned_approach_but_not_absence_check(self):
        goal = ObjectGoal("stock", "apple", "food", 100, 0, 0)
        self.behavior.advance(goal, blocked=False)
        self.acknowledge()
        self.assertIsInstance(self.behavior.advance(None, blocked=False), Hold)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.completed, [("stock", False)])

    def test_continuing_wish_uses_offer_threshold_and_cannot_leak_to_other_record(self):
        set_test_pet_values(self.state, satiety=80)
        goal = self.awareness.intentions.assess_offer(
            self.awareness.memory.snapshot()[0], self.state,
        )
        self.assertTrue(goal.consume)
        self.assertTrue(self.behavior.decide("stock", ObjectUseContext.SUPPLY).consume)
        alternate = self.alternative()
        self.assertFalse(self.behavior.decide(
            alternate.token, ObjectUseContext.SUPPLY,
        ).consume)

    def test_lost_unknown_target_is_retired_without_a_patrol(self):
        set_test_pet_values(self.state, satiety=100)
        self.awareness.memory.restore_snapshot(())
        self.awareness.memory.update((ObjectObservation(
            "stock", None, None, 100, 0, True, 0,
        ),), now=0)
        self.interaction.begin_goal(ObjectGoal(
            "stock", None, None, 100, 0, 0, "investigate",
        ))
        self.acknowledge()
        self.interaction.start_search()
        self.assertFalse(self.interaction.active)
        self.assertIsNone(self.awareness.memory.get("stock"))
        self.assertNotIn("object_search", [cue.event for cue in self.cues])

    def test_confirmed_unknown_absence_has_one_readable_notice_then_forgets(self):
        self.awareness.memory.restore_snapshot(())
        self.awareness.memory.update((ObjectObservation(
            "unknown", None, None, 100, 0, True, 0,
        ),), now=0)
        self.observe()
        self.now = .6
        noticed = self.observe()
        self.assertTrue(noticed.absence_noticed)
        self.assertEqual(self.interaction.phase, "notice_absence")
        self.assertIsNone(self.cues[-1].identity)
        self.acknowledge()
        self.assertIsNone(self.awareness.memory.get("unknown"))
        self.assertFalse(self.interaction.active)
        self.assertEqual([cue.event for cue in self.cues], ["object_place_missing"])

    def test_identified_loss_precedes_pending_unknown_loss(self):
        self.awareness.memory.restore_snapshot(())
        self.awareness.memory.update((
            ObjectObservation("unknown", None, None, 100, 0, True, 0),
            ObjectObservation("known", "apple", "food", 150, 0, True, 0),
        ), now=0)
        self.observe()
        self.now = .6
        self.observe()
        self.finish_orientation()
        self.assertEqual(self.interaction.memory_id, "known")
        self.acknowledge()
        self.assertTrue(self.interaction.searching)

    def test_satisfied_need_does_not_abort_an_ongoing_missing_item_search(self):
        self.start_search()
        set_test_pet_values(self.state, satiety=100)
        self.assertIsInstance(self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 100),
        ), SearchMotion)
        self.assertTrue(self.interaction.active)
        self.assertEqual(self.completed, [])
        known = self.awareness.memory.get("stock")
        assert known is not None
        self.assertEqual((known.identity, known.place_status), ("apple", "missing"))
        self.acknowledge()
        self.now = 2.1
        self.interaction.update()
        self.assertEqual(self.interaction.phase, "search")
        self.interaction.search_destination(SearchPosition(50, 750, 50))
        self.interaction.search_destination(SearchPosition(50, 750, 750))
        self.interaction.complete_search()
        self.assertEqual(self.interaction.phase, "missing")
        self.assertEqual(self.actions, [])

    def test_blocking_pauses_search_and_explicit_interruption_cancels_it(self):
        self.start_search()
        observation = self.observe(facts=BehaviorFacts(character_action_busy=True))
        self.assertFalse(observation.blocked)
        self.assertIsInstance(self.behavior.advance_search(
            blocked=observation.blocked, position=SearchPosition(50, 750, 100),
        ), SearchMotion)
        self.assertTrue(self.interaction.acknowledge_contact())
        self.interaction.update()
        contact = self.cues[-1]
        self.assertEqual(contact.event, "object_busy_search")
        self.assertTrue(self.interaction.contact_feedback_active)
        self.assertIsInstance(self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 50),
        ), SearchMotion)
        self.assertEqual(self.interaction.search_progress, .5)
        self.assertEqual(self.interaction.memory_id, "stock")
        first = self.awareness.memory.get("stock")
        assert first is not None
        self.interaction.notice_absence(replace(first, token="another"))
        self.interaction.update()
        required = self.cues[-1]
        self.assertEqual(required.event, "object_place_missing")
        self.assertFalse(self.interaction.contact_feedback_active)
        for completed in (False, True):
            self.interaction.receive_feedback(FeedbackReceipt(contact.key, completed))
            self.assertFalse(self.interaction.search_ready)
        self.assertEqual(self.behavior.advance_search(blocked=False), Hold())
        self.acknowledge()
        self.assertTrue(self.interaction.search_ready)
        self.assertEqual(self.interaction.search_progress, .5)
        self.assertIsInstance(self.behavior.advance_search(blocked=True), Hold)
        self.assertTrue(self.interaction.search_active)
        self.interaction.interrupt(lambda: None)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.completed, [("stock", False)])

    def test_verified_reunion_waits_for_its_own_feedback(self):
        self.start_search()
        old = self.interaction.feedback_key
        goal = self.alternative(observed=True)
        self.assertIsInstance(self.behavior.advance_search(blocked=False), Hold)
        self.assertEqual(self.interaction.phase, "found")
        self.assertEqual(self.cues[-1].record_id, goal.token)
        self.interaction.receive_feedback(FeedbackReceipt(old, True))
        self.interaction.update()
        self.assertEqual(self.interaction.phase, "found")
        self.acknowledge()
        self.assertFalse(self.interaction.active)
        self.assertFalse(self.interaction.search_active)
        self.assertEqual(self.completed, [(goal.token, False)])
        self.assertEqual(self.actions, [])

    def test_search_investigates_unknown_find_and_resumes_its_route(self):
        other = self.world.place_resting("apple", 180, ObjectFootprint(8, 8))
        self.observe()
        self.now = .3
        first = self.observe()
        self.assertFalse(first.absence_noticed)
        self.assertFalse(self.interaction.active)
        self.now = .5
        missing = self.finish_orientation()
        self.assertTrue(missing.absence_noticed)
        self.assertEqual(self.cues[-1].event, "object_place_missing")
        self.acknowledge()
        self.assertEqual(self.interaction.phase, "search")
        self.acknowledge()
        self.interaction.search_destination(SearchPosition(50, 750, 50))
        self.now += .3
        observation = self.observe()
        self.assertIsNone(observation.goal)  # Search owns the next investigation.
        self.assertIsInstance(self.behavior.advance_search(
            blocked=observation.blocked,
        ), Hold)
        investigation = self.awareness.intentions.goal
        assert investigation is not None
        self.assertNotEqual(investigation.token, "stock")
        self.assertEqual(investigation.purpose, "investigate")
        self.assertEqual(self.interaction.phase, "approach")
        self.assertTrue(self.interaction.search_active)
        self.assertEqual(self.cues[-1].event, "object_approach")
        self.assertNotIn("object_notice", [cue.event for cue in self.cues])
        self.assertNotIn("object_found", [cue.event for cue in self.cues])
        self.assertIsNotNone(self.awareness.record_for_instance(other.instance_id))
        self.assertEqual(self.interaction.memory_id, investigation.token)
        self.assertEqual(self.interaction.search_progress, .5)
        # Native reach failure retires this attempt while the same pass survives.
        self.behavior.unreachable(now=self.now)
        self.assertEqual(self.interaction.phase, "search")
        self.assertEqual(self.interaction.memory_id, "stock")
        self.assertEqual(self.interaction.search_progress, .5)
        self.assertFalse(self.interaction.can_investigate(investigation.token))

    def test_route_needs_actual_arrival_at_both_ends_before_failure(self):
        self.start_search()
        self.acknowledge()
        for stamp in (1, 20, 200):
            self.now = stamp
            motion = self.behavior.advance_search(
                blocked=False, position=SearchPosition(50, 750, 200),
            )
            self.assertEqual(motion, SearchMotion(50, 0))
        self.assertEqual(self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 50),
        ), SearchMotion(750, .5))
        self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 749),
        )
        self.assertEqual(self.interaction.phase, "missing")
        self.acknowledge()
        self.assertFalse(self.interaction.active)

    def test_right_start_and_changed_bounds_require_current_route_coverage(self):
        self.start_search()
        self.acknowledge()
        self.assertEqual(self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 700),
        ), SearchMotion(750, 0))
        self.behavior.advance_search(
            blocked=False, position=SearchPosition(50, 750, 750),
        )
        self.assertEqual(self.behavior.advance_search(
            blocked=False, position=SearchPosition(100, 1400, 750),
        ), SearchMotion(100, 0))

    def test_matching_known_find_is_resolved_even_when_no_longer_needed(self):
        self.start_search()
        set_test_pet_values(self.state, satiety=100)
        goal = self.alternative(observed=True)
        self.awareness.memory.mark_assessed(goal.token)
        self.behavior.advance_search(blocked=False)
        self.assertEqual(self.interaction.phase, "found")
        self.acknowledge()
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.actions, [])

    def test_missing_or_unidentified_record_cannot_resolve_search(self):
        self.start_search()
        self.awareness.memory.update((ObjectObservation(
            "unknown", None, None, 240, 0, True, 0,
        ),), now=0)
        for token in ("unknown", "no_record"):
            with self.subTest(token=token):
                self.assertFalse(self.interaction.found(token))
                self.assertEqual(self.interaction.memory_id, "stock")
                self.assertEqual(self.cues[-1].event, "object_search")

    def test_both_distant_losses_are_collected_before_any_notice_or_new_action(self):
        self.awareness.memory.restore_snapshot(())
        records = []
        for x in (50, 750):
            item = self.world.place_resting("apple", x, ObjectFootprint(8, 8))
            record = self.awareness.memory.observe_find(ObjectObservation(
                "learned", "apple", "food", x, 0, True, 0, True,
            ), now=0, record=None, claimed=frozenset(), maximum_distance=0,
                instance_id=item.instance_id)
            records.append(record)
            self.world.move_resting(item.instance_id, x + 60 if x < 400 else x - 60,
                                    expected_revision=item.revision)
        known = self.awareness.memory.get(records[0])
        assert known is not None
        self.awareness.intentions.assess_offer(known, self.state)
        wish = self.awareness.intentions.goal
        assert wish is not None
        self.behavior.request_orientation()
        sides = []
        observation = None
        for _ in range(20):
            sides.append(self.behavior.orientation_side)
            observation = self.observe(x=400, width=30)
            if observation.absence_noticed:
                break
            self.assertEqual(self.behavior.advance(
                observation.goal, blocked=observation.blocked,
            ), Hold())
            self.assertEqual(self.awareness.intentions.goal, wish)
            self.assertFalse(self.interaction.active)
            self.now += .2
        self.assertIn(-1, sides)
        self.assertIn(1, sides)
        assert observation is not None
        self.assertTrue(observation.absence_noticed)
        self.assertEqual({item.token for item in self.awareness.memory.snapshot()
                          if item.place_status == "missing"}, set(records))
        self.assertEqual(len(self.awareness.memory.snapshot()), 2)
        self.assertEqual([cue.event for cue in self.cues], ["object_place_missing"])
        self.acknowledge()
        self.acknowledge()
        self.assertEqual([cue.record_id for cue in self.cues
                          if cue.event == "object_place_missing"], records)
        self.assertTrue(self.interaction.search_active)

    def test_orientation_pauses_a_valid_wish_and_resumes_it_after_both_looks(self):
        item, goal = self.observed_stock()
        self.awareness.memory.mark_assessed(goal.token)
        known = self.awareness.memory.get(goal.token)
        assert known is not None
        self.awareness.intentions.assess_offer(known, self.state)
        wish = self.awareness.intentions.goal
        assert wish is not None
        self.behavior.request_orientation()
        observation = None
        for _ in range(20):
            observation = self.observe()
            if self.behavior.orientation_side is None:
                break
            self.assertIsNone(observation.goal)
            self.assertEqual(self.awareness.intentions.goal, wish)
            self.assertFalse(self.interaction.active)
            self.now += .2
        assert observation is not None and observation.goal is not None
        self.assertEqual(observation.goal.token, wish.token)
        self.behavior.advance(observation.goal, blocked=observation.blocked)
        self.assertEqual(self.interaction.memory_id, wish.token)
        self.assertEqual(self.awareness.instance_for_record(wish.token),
                         item.instance_id)
        self.assertEqual(self.cues[-1].event, "object_collect_wanted")

    def prepare_unknown_discovery(self, side):
        self.awareness.memory.restore_snapshot(())
        set_test_pet_values(self.state, satiety=100, energy=100)
        stock = self.world.place_resting("apple", 400, ObjectFootprint(8, 8))
        record = self.awareness.memory.observe_find(ObjectObservation(
            "earlier", "apple", "food", 400, 0, True, 0,
        ), now=0, record=None, claimed=frozenset(), maximum_distance=0,
            instance_id=stock.instance_id)
        self.awareness.memory.mark_assessed(record)
        items = [self.world.place_resting("apple", 400 + side * offset,
                                         ObjectFootprint(8, 8))
                 for offset in (150, 220)]
        self.discovery_gaze = None
        return items

    def sample_unknown_discovery(self, side):
        self.interaction.update()
        target = self.discovery_gaze
        attention = replace(choose_object_attention(
            self.interaction.phase, sleeping=False, game_open=False, walking=0,
            orientation_side=self.behavior.orientation_side,
            cursor=(side, 0) if self.now < .5 else None,
            target=((target.x - 400) / 100, (target.height - 60) / 100)
            if target is not None else None,
        ), origin=(400, 60), width=100)
        observation = self.behavior.observe(
            self.world.snapshot(), now=self.now, x=400, width=100,
            presentation=None, facts=BehaviorFacts(), attention=attention,
        )
        self.discovery_gaze = observation.gaze
        motion = self.behavior.advance(observation.goal, blocked=observation.blocked)
        return observation, attention, motion

    def test_new_unknown_investigation_survives_both_looks_and_rechecks_its_item(self):
        for side in (-1, 1):
            with self.subTest(side=side):
                self.setUp()
                items = self.prepare_unknown_discovery(side)
                token = None
                looks = set()
                returned_to_item = False
                for step in range(60):
                    self.now = step * .1
                    observation, attention, motion = self.sample_unknown_discovery(side)
                    if self.behavior.orientation_side is not None:
                        looks.add(self.behavior.orientation_side)
                        goal = self.awareness.intentions.goal
                        assert goal is not None
                        token = token or goal.token
                        self.assertEqual((goal.token, goal.purpose),
                                         (token, "investigate"))
                        self.assertIsNone(observation.goal)
                        self.assertIsInstance(motion, Hold)
                    elif token is not None:
                        self.assertEqual(observation.gaze,
                                         GazeTarget(400 + side * 150, 0))
                        returned_to_item = True
                    self.assertFalse(self.interaction.search_active)
                    if self.interaction.active:
                        assert token is not None
                        self.assertEqual(self.interaction.phase, "notice")
                        self.assertEqual(self.interaction.memory_id, token)
                        self.assertEqual(
                            self.awareness.instance_for_record(token),
                            items[0].instance_id,
                        )
                        self.assertTrue(attention.sees(400 + side * 150, 0))
                        known = self.awareness.memory.get(token)
                        assert known is not None
                        self.assertIsNone(known.identity)
                        self.assertEqual(known.observed_at, self.now)
                        break
                else:
                    self.fail("New-item investigation never resumed after orientation")
                self.assertEqual(looks, {-1, 1})
                self.assertTrue(returned_to_item)
                self.assertEqual([cue.event for cue in self.cues], ["object_notice"])
                self.acknowledge()
                self.assertEqual(self.cues[-1].event, "object_approach")
                self.acknowledge()
                self.assertEqual(self.interaction.phase, "approach")
                self.assertFalse(self.interaction.search_active)

    def test_removed_new_item_during_orientation_does_not_start_lost_stock_search(self):
        for side in (-1, 1):
            with self.subTest(side=side):
                self.setUp()
                items = self.prepare_unknown_discovery(side)
                token = None
                removed = False
                looked_back = False
                for step in range(60):
                    self.now = step * .1
                    observation, _attention, motion = self.sample_unknown_discovery(
                        side,
                    )
                    if not removed and self.behavior.orientation_side == -1:
                        goal = self.awareness.intentions.goal
                        assert goal is not None
                        token = goal.token
                        self.world.remove(items[0].instance_id,
                                          expected_revision=items[0].revision)
                        removed = True
                    if removed and self.behavior.orientation_side is None:
                        looked_back |= observation.gaze == GazeTarget(
                            400 + side * 150, 0,
                        )
                    self.assertIsInstance(motion, Hold)
                    self.assertFalse(self.interaction.search_active)
                    if self.cues:
                        self.assertEqual(self.cues[-1].event, "object_place_missing")
                        self.assertIsNone(self.cues[-1].identity)
                        self.acknowledge()
                    if removed and token is not None and (
                        self.awareness.memory.get(token) is None
                    ):
                        break
                self.assertTrue(removed)
                self.assertTrue(looked_back)
                self.assertIsNone(self.awareness.intentions.goal)
                self.assertFalse(self.interaction.active)
                self.assertEqual([cue.event for cue in self.cues],
                                 ["object_place_missing"])

    def test_pending_new_item_outside_notice_range_is_released_without_patrol(self):
        self.prepare_unknown_discovery(-1)
        token = None
        for step in range(60):
            self.now = step * .1
            self.sample_unknown_discovery(-1)
            goal = self.awareness.intentions.goal
            if self.behavior.orientation_side is not None:
                assert goal is not None
                token = goal.token
            elif token is not None:
                break
        assert token is not None
        self.assertFalse(self.interaction.active)
        # Relocation / a smaller sprite can put the remembered unknown place
        # outside the actual range. It must not hold a permanent look request.
        self.now += .1
        observation = self.behavior.observe(
            self.world.snapshot(), now=self.now, x=750, width=50,
            presentation=None, facts=BehaviorFacts(),
            attention=ObjectAttention("survey", None, origin=(750, 30), width=50),
        )
        self.assertIsNone(observation.goal)
        self.assertIsNone(observation.gaze)
        self.assertIsNone(self.awareness.intentions.goal)
        self.assertIsInstance(self.behavior.advance(
            observation.goal, blocked=observation.blocked,
        ), Hold)
        self.assertFalse(self.interaction.search_active)
        known = self.awareness.memory.get(token)
        assert known is not None
        self.assertEqual(known.place_status, "remembered")
        self.assertEqual(self.cues, [])

    def test_interrupted_right_look_requires_fresh_both_sides_after_release(self):
        for transport in (False, True):
            with self.subTest(transport=transport):
                self.setUp()
                self.awareness.memory.restore_snapshot(())
                set_test_pet_values(self.state, satiety=100)
                portions = [self.world.place_resting("apple", x, ObjectFootprint(8, 8))
                            for x in (200, 600)]
                for item in portions:
                    assert item.position is not None
                    record = self.awareness.memory.observe_find(ObjectObservation(
                        "earlier", "apple", "food", item.position.x, 0, True, 0, True,
                    ), now=0, record=None, claimed=frozenset(), maximum_distance=0,
                        instance_id=item.instance_id)
                    self.awareness.memory.mark_assessed(record)

                def sample(now, *, activity=False):
                    self.now = now
                    following = self.awareness.following_record
                    known = (self.awareness.memory.get(following)
                             if following is not None else None)
                    attention = replace(choose_object_attention(
                        "idle", sleeping=False, game_open=False, walking=0,
                        following_cursor=following is not None,
                        orientation_side=self.behavior.orientation_side,
                        activity_active=activity, cursor=(2, 0),
                        target=((known.x - 400) / 100, (known.height - 60) / 100)
                        if known is not None else None,
                    ), origin=(400, 60), width=100)
                    snapshot = self.world.snapshot()
                    observation = self.behavior.observe(
                        snapshot, now=now, x=400, width=100, presentation=None,
                        facts=BehaviorFacts(carrying=any(
                            item.state == ObjectState.USER_HELD
                            for item in snapshot.objects
                        )), attention=attention,
                    )
                    return observation, attention

                self.behavior.request_orientation()
                sample(0)
                sample(.5)
                self.assertEqual(self.behavior.orientation_side, 1)
                _, right = sample(.6)
                held = None
                if transport:
                    held = self.world.take_resting(portions[1].instance_id,
                                                   expected_revision=0)
                    self.assertIsNotNone(self.awareness.witness_take(
                        held.instance_id, position=(600, 0), now=.9, attention=right,
                    ))
                observation, attention = sample(.9, activity=not transport)
                self.assertEqual(attention.mode,
                                 "object" if transport else "unavailable")
                self.assertTrue(observation.blocked)
                self.assertEqual(self.awareness.absences, ())
                if held is not None:
                    self.world.return_user_held(held.instance_id, 600,
                                                expected_revision=held.revision)
                sample(1)
                sample(1.1)
                self.assertEqual(self.behavior.orientation_side, -1)
                sample(1.4)
                self.assertEqual(self.behavior.orientation_side, -1)
                sample(1.6)
                self.assertEqual(self.behavior.orientation_side, 1)
                sample(1.7)
                sample(2)
                self.assertEqual(self.behavior.orientation_side, 1)
                sample(2.2)
                self.assertIsNone(self.behavior.orientation_side)
                self.assertEqual(self.cues, [])
                self.assertEqual(self.awareness.absences, ())
                self.assertEqual(len(self.awareness.memory.snapshot()), 2)
                self.assertTrue(all(known.recognized
                                    for known in self.awareness.memory.snapshot()))
