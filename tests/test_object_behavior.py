from tools.pet_test_support import set_test_pet_values
"""Behavior coordination uses real application owners without a desktop or Tk."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.application.object_behavior import (
    Approach,
    BehaviorFacts,
    GazeTarget,
    Hold,
    ObjectBehaviorCoordinator,
    SearchMotion,
    SearchStopped,
)
from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
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


class ObjectBehaviorTests(unittest.TestCase):
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
            completed=completed, memory=self.awareness.memory,
            decide=lambda token, context: self.behavior.decide(token, context),
            feedback=feedback, cancel_feedback=lambda: None, now=lambda: self.now,
            inspection_seconds=1, search_seconds=2,
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

    def alternative(self, *, kind: ConsumableKind = "food"):
        identity = "apple" if kind == "food" else "energy_drink"
        self.awareness.memory.update((ObjectObservation(
            "alternative", identity, kind, 240, 0, True, 0,
        ),), now=0)
        return ObjectGoal("alternative", identity, kind, 240, 0, 0, "investigate")

    def observe(self, *, facts=BehaviorFacts(), x=100, width=100):
        self.interaction.update()
        return self.behavior.observe(
            self.world.snapshot(), now=self.now, x=x, width=width,
            presentation=None, facts=facts,
        )

    def observed_stock(self):
        self.awareness.memory.restore_snapshot(())
        item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.observe()
        self.now = .3
        observation = self.observe()
        assert observation.goal is not None
        goal = observation.goal
        self.awareness.memory.update((ObjectObservation(
            goal.token, "apple", "food", 100, 0, True, self.now,
        ),), now=self.now)
        return item, replace(goal, identity="apple", kind="food")

    def test_absence_precedes_discovery_and_only_acknowledges_accepted_notice(self):
        self.world.place_resting("apple", 180, ObjectFootprint(8, 8))
        self.observe()
        self.now = .5
        waiting = self.observe(facts=BehaviorFacts(user_action_pending=True))
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
        self.observe(facts=BehaviorFacts(user_action_pending=True))
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
        for facts in (BehaviorFacts(carrying=True), BehaviorFacts(controls_active=True),
                      BehaviorFacts(game_open=True), BehaviorFacts(playback_busy=True)):
            with self.subTest(facts=facts):
                self.assertTrue(self.observe(facts=facts).blocked)
        self.interaction.begin_goal(ObjectGoal("stock", "apple", "food", 100, 0, 0))
        self.assertFalse(self.observe(facts=BehaviorFacts(
            carrying=True, controls_active=True,
        )).blocked)
        self.assertTrue(self.observe(facts=BehaviorFacts(game_open=True)).blocked)
        set_test_pet_values(self.state, sleeping=True)
        self.assertTrue(self.observe().blocked)

    def test_blocked_nearest_unassessed_observation_keeps_gaze_without_episode(self):
        self.awareness.memory.restore_snapshot(())
        self.world.place_resting("apple", 180, ObjectFootprint(8, 8))
        self.world.place_resting("apple", 130, ObjectFootprint(8, 8))
        facts = BehaviorFacts(controls_active=True)
        self.observe(facts=facts)
        self.now = .3
        observation = self.observe(facts=facts)
        self.assertIsNone(observation.goal)
        self.assertEqual(observation.gaze, GazeTarget(130, 0))
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

    def test_changed_approach_finishes_old_episode_before_new_notice(self):
        old = ObjectGoal("stock", "apple", "food", 100, 0, 0)
        self.behavior.advance(old, blocked=False)
        self.acknowledge()
        new = self.alternative()
        self.assertIsInstance(self.behavior.advance(new, blocked=False), Hold)
        self.assertEqual(self.completed, [("stock", False)])
        self.assertEqual(self.interaction.memory_id, new.token)
        self.assertEqual(self.interaction.phase, "notice")
        self.assertEqual(self.actions, [])

    def test_synchronous_replacement_can_approach_in_the_same_update(self):
        self.start_search()
        goal = self.alternative()
        self.synchronous_feedback = True
        self.assertEqual(self.behavior.advance(goal, blocked=False), Approach(goal))
        self.assertEqual(self.interaction.phase, "approach")
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

    def test_lost_return_binding_starts_search_but_holds_for_this_update(self):
        goal = ObjectGoal("stock", "apple", "food", 100, 0, 0)
        self.behavior.advance(goal, blocked=False)
        self.assertTrue(self.interaction.target_taken(goal.token))
        self.assertIsInstance(self.behavior.advance(goal, blocked=True), Hold)
        self.assertEqual(self.interaction.phase, "search")
        self.assertIsInstance(self.behavior.advance(None, blocked=False), SearchMotion)

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

    def test_native_reach_alone_cannot_authorize_an_unseen_or_stale_offer(self):
        item, goal = self.observed_stock()

        def allowed(*, reachable=True, ready=True, now=.3, facts=BehaviorFacts()):
            return self.behavior.can_acquire(
                item.instance_id, object_state=ObjectState.USER_HELD,
                reachable=reachable, offer_ready=ready, now=now, facts=facts,
            )

        self.assertTrue(allowed())
        self.assertFalse(allowed(reachable=False))
        self.assertFalse(allowed(ready=False))
        self.assertFalse(allowed(now=.8))
        self.assertFalse(allowed(facts=BehaviorFacts(playback_busy=True)))
        self.assertFalse(allowed(facts=BehaviorFacts(game_open=True)))
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

    def test_non_search_phase_is_left_to_the_remaining_update(self):
        goal = self.alternative()
        self.assertIsNone(self.behavior.advance_search(goal, blocked=True))
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.cues, [])
        self.assertEqual(self.completed, [])

    def test_wanted_stock_continues_with_relative_center_and_active_progress(self):
        self.start_search()
        self.now = 1
        key = self.interaction.feedback_key
        self.assertEqual(self.behavior.advance_search(None, blocked=False),
                         SearchMotion(100, .5))
        self.assertEqual(self.interaction.feedback_key, key)
        self.assertEqual(self.completed, [])
        self.assertEqual(self.actions, [])

    def test_unknown_stock_is_not_cancelled_by_satisfied_needs(self):
        set_test_pet_values(self.state, satiety=100)
        self.start_search(identified=False)
        self.assertIsInstance(self.behavior.advance_search(None, blocked=False),
                              SearchMotion)
        self.assertTrue(self.interaction.searching)
        self.assertEqual(self.completed, [])

    def test_changed_need_stops_once_and_preserves_learned_missing_stock(self):
        self.start_search()
        set_test_pet_values(self.state, satiety=100)
        self.assertIsInstance(self.behavior.advance_search(None, blocked=False),
                              SearchStopped)
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.completed, [("stock", False)])
        known = self.awareness.memory.get("stock")
        assert known is not None
        self.assertEqual((known.identity, known.place_status), ("apple", "missing"))
        self.assertIsNone(self.behavior.advance_search(None, blocked=False))
        self.assertEqual(self.completed, [("stock", False)])
        self.assertEqual(self.actions, [])

    def test_blocking_cancels_then_leaves_the_desktop_update_to_continue(self):
        self.start_search()
        self.assertIsNone(self.behavior.advance_search(None, blocked=True))
        self.assertFalse(self.interaction.active)
        self.assertEqual(self.completed, [("stock", False)])

    def test_replacement_precedes_blocking_and_waits_for_its_own_feedback(self):
        self.start_search()
        old = self.interaction.feedback_key
        goal = self.alternative()
        self.assertIsNone(self.behavior.advance_search(goal, blocked=True))
        self.assertEqual(self.interaction.phase, "found")
        self.assertEqual(self.cues[-1].record_id, goal.token)
        self.interaction.receive_feedback(FeedbackReceipt(old, True))
        self.interaction.update()
        self.assertEqual(self.interaction.phase, "found")
        self.acknowledge()
        self.assertEqual(self.interaction.memory_id, goal.token)
        self.assertNotEqual(self.interaction.feedback_key.interaction_id,
                            old.interaction_id)
        self.assertEqual(self.completed, [])
        self.assertEqual(self.actions, [])

    def test_synchronous_replacement_keeps_the_same_update_handoff(self):
        self.start_search()
        goal = self.alternative()
        self.synchronous_feedback = True
        self.assertIsNone(self.behavior.advance_search(goal, blocked=False))
        self.assertEqual(self.interaction.phase, "approach")
        self.assertEqual(self.interaction.memory_id, goal.token)
        self.assertEqual(self.completed, [])
        self.assertEqual(self.actions, [])

    def test_same_target_is_not_a_replacement(self):
        self.start_search()
        key = self.interaction.feedback_key
        goal = ObjectGoal("stock", "apple", "food", 100, 0, 0)
        self.assertIsInstance(self.behavior.advance_search(goal, blocked=False),
                              SearchMotion)
        self.assertEqual(self.interaction.feedback_key, key)

    def test_goal_identity_cannot_replace_missing_or_unidentified_memory(self):
        self.start_search()
        self.awareness.memory.update((ObjectObservation(
            "unknown", None, None, 240, 0, True, 0,
        ),), now=0)
        for token in ("unknown", "no_record"):
            with self.subTest(token=token):
                forged = ObjectGoal(token, "apple", "food", 240, 0, 0)
                self.assertIsInstance(
                    self.behavior.advance_search(forged, blocked=False), SearchMotion,
                )
                self.assertEqual(self.interaction.memory_id, "stock")
                self.assertEqual(self.cues[-1].event, "object_search")

    def test_unwanted_alternative_does_not_replace_a_wanted_search(self):
        self.start_search()
        goal = self.alternative(kind="drink")
        self.assertIsInstance(self.behavior.advance_search(goal, blocked=False),
                              SearchMotion)
        self.assertEqual(self.interaction.memory_id, "stock")
        self.assertEqual(self.completed, [])
