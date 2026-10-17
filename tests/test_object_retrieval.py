"""Known stock bypasses repeated inquiry while custody/use gates remain intact."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.mind.object_decisions import ObjectUseContext, decide_object_use
from aiko_pet.pet.mind.object_intentions import ObjectGoal, ObjectIntentions
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectRetrievalTests(unittest.TestCase):
    def test_early_absence_waits_for_receipt_then_uses_one_search_budget(self):
        goal = ObjectIntentions().choose(self.memory.snapshot(), self.pet, x=0, now=0)
        assert goal is not None
        self.coordinator.begin_goal(goal)
        known = self.memory.get(self.item.instance_id)
        assert known is not None
        self.memory.mark_missing(known.token)
        previous = self.cues[-1]
        self.assertTrue(self.coordinator.notice_absence(known))
        self.assertEqual(self.coordinator.phase, "notice_absence")
        self.assertEqual(self.cues[-1].event, "object_place_missing")
        self.assertFalse(self.coordinator.notice_absence(known))
        self.coordinator.receive_feedback(FeedbackReceipt(previous.key, True))
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "notice_absence")
        self.stamp = 3
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "search")
        self.stamp = 4.9
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "search")
        self.stamp = 5.1
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "missing")
        self.acknowledge()
        self.assertEqual(self.done, [(known.token, False)])

    def take_unknown_drink(self):
        self.item = self.world.place_resting("energy_drink", 100, ObjectFootprint(8, 8))
        self.memory.restore_snapshot(())
        self.memory.update((ObjectObservation(
            self.item.instance_id, None, None, 100, 0, True, 0,
        ),), now=0)
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, None, None, 100, 0, 0, "investigate",
        ))
        self.acknowledge()
        self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.coordinator.target_taken(self.item.instance_id)
        self.memory.update((ObjectObservation(
            self.item.instance_id, "energy_drink", "drink", 100, 80, False, 1,
        ),), now=1)
        self.memory.mark_assessed(self.item.instance_id)
        self.acknowledge()

    def test_taken_unknown_offer_is_identified_then_wanted_before_handover(self):
        self.take_unknown_drink()
        decision = decide_object_use(self.memory.get(self.item.instance_id),
                                     self.pet, ObjectUseContext.OFFER)
        self.coordinator.observe_held_offer(self.item.instance_id, decision)
        recognition = self.cues[-1]
        self.assertEqual(recognition.event, "object_recognized")
        self.assertEqual(recognition.identity, "energy_drink")
        self.assertEqual(self.coordinator.phase, "recognize_offer")
        self.assertEqual(self.consumed, [])
        self.acknowledge()
        self.assertEqual(self.cues[-1].event, "object_offer")
        self.assertEqual(self.coordinator.phase, "decide_offer")
        self.acknowledge()
        self.coordinator.receive_feedback(FeedbackReceipt(recognition.key, True))
        self.assertEqual(self.coordinator.phase, "await_return")
        self.assertTrue(self.coordinator.offer_on_release(self.item.instance_id))
        self.assertEqual(self.consumed, [])
        self.acknowledge()
        self.assertEqual(self.consumed[0][2], ConsumptionOrigin.HANDOVER)

    def test_taken_offer_refusal_ends_return_requests_without_collecting(self):
        self.take_unknown_drink()
        self.pet.energy = 100
        decision = decide_object_use(self.memory.get(self.item.instance_id),
                                     self.pet, ObjectUseContext.OFFER)
        self.coordinator.observe_held_offer(self.item.instance_id, decision)
        self.acknowledge()
        self.assertEqual(self.cues[-1].event, "object_refuse")
        self.acknowledge()
        self.stamp = 100
        self.coordinator.observe_target_state(ObjectState.USER_HELD)
        self.coordinator.update()
        self.assertFalse(self.coordinator.active)
        self.assertEqual(self.done, [(self.item.instance_id, False)])
        self.assertEqual(self.consumed, [])
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.USER_HELD)
        self.assertEqual(self.cues[-1].event, "object_refuse")

    def test_need_changes_during_recognition_and_decision_keep_current_feedback(self):
        self.take_unknown_drink()
        known = self.memory.get(self.item.instance_id)
        self.coordinator.observe_held_offer(
            self.item.instance_id, decide_object_use(known, self.pet,
                                                     ObjectUseContext.OFFER),
        )
        self.pet.energy = 100
        self.coordinator.observe_held_offer(
            self.item.instance_id, decide_object_use(known, self.pet,
                                                     ObjectUseContext.OFFER),
        )
        self.acknowledge()
        self.assertEqual(self.cues[-1].event, "object_refuse")
        refused = self.cues[-1].key
        self.pet.energy = 65
        self.coordinator.observe_held_offer(
            self.item.instance_id, decide_object_use(known, self.pet,
                                                     ObjectUseContext.OFFER),
        )
        self.acknowledge()
        self.assertEqual(self.cues[-1].event, "object_offer")
        self.coordinator.receive_feedback(FeedbackReceipt(refused, True))
        self.assertEqual(self.coordinator.phase, "decide_offer")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "await_return")
        self.assertEqual(self.consumed, [])

    def test_drop_during_offer_recognition_keeps_reading_then_resumes_pickup(self):
        self.take_unknown_drink()
        self.coordinator.observe_held_offer(
            self.item.instance_id,
            decide_object_use(self.memory.get(self.item.instance_id), self.pet,
                              ObjectUseContext.OFFER),
        )
        held = self.world.get(self.item.instance_id)
        self.world.return_user_held(held.instance_id, 110,
                                    expected_revision=held.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.assertEqual(self.coordinator.phase, "recognize_offer")
        self.acknowledge()
        self.acknowledge()
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.acknowledge()
        self.coordinator.arrive()
        self.grasp()
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertEqual(self.consumed[0][2], ConsumptionOrigin.AUTONOMOUS)
        self.assertNotIn("object_inspect", [cue.event for cue in self.cues])

    def setUp(self):
        self.world = WorldState(WorldSurface(800, 600), (
            ObjectDefinition("apple", "apple", "apple",
                             frozenset((ObjectInteraction.EAT,))),
            ObjectDefinition("energy_drink", "energy_drink", None,
                             frozenset((ObjectInteraction.DRINK,))),
        ))
        self.item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.memory = ObjectMemory()
        self.seen = ObjectObservation(self.item.instance_id, "apple", "food",
                                      100, 0, True, 0)
        self.memory.update((self.seen,), now=0)
        self.memory.mark_assessed(self.item.instance_id)
        self.memory.note_placement(self.item.instance_id, x=100, height=0,
                                   now=0, deferred=True)
        self.pet = PetState(satiety=50, energy=40)
        self.cues, self.actions, self.consumed, self.done = [], [], [], []
        self.stamp = 0

        def play(clip):
            self.actions.append(clip)
            return len(self.actions)

        def consume(key, token, memory_id, origin):
            self.consumed.append((key, token, origin))
            item = self.world.get(token)
            self.world.consume(token, expected_revision=item.revision)
            self.memory.forget(token)
            return True

        self.coordinator = ObjectInteractionCoordinator(
            self.world, play=play, stop=lambda: None, select_item=lambda _item: None,
            consume=consume, can_acquire=lambda _token: True,
            ground_x=lambda _token: 110,
            completed=lambda token, used: self.done.append((token, used)),
            memory=self.memory,
            resolve_instance=lambda token: token,
            record_for_instance=lambda token: token,
            decide=lambda token, origin: decide_object_use(
                self.memory.get(token), self.pet, origin,
            ), feedback=self.cues.append, cancel_feedback=lambda: None,
            now=lambda: self.stamp, inspection_seconds=1, search_seconds=2,
        )

    def acknowledge(self):
        self.coordinator.receive_feedback(FeedbackReceipt(self.cues[-1].key, True))
        self.coordinator.update()

    def begin_retrieval(self):
        goal = ObjectIntentions().choose(self.memory.snapshot(), self.pet, x=0, now=0)
        assert goal is not None
        self.assertEqual(goal.purpose, "consume")
        self.assertTrue(self.coordinator.begin_goal(goal))
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "approach")
        self.coordinator.arrive()
        self.assertEqual(self.coordinator.phase, "pick_up")

    def grasp(self):
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))

    def finish_pickup(self):
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))

    def test_remembered_food_skips_inquiry_but_waits_for_full_consumption_clip(self):
        self.begin_retrieval()
        self.assertEqual(self.cues[0].event, "object_recall_saved_food")
        self.grasp()
        self.assertEqual(self.consumed, [])
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertEqual(self.actions, ["pick_up", "eat"])
        self.grasp()
        self.finish_pickup()
        self.assertEqual(len(self.consumed), 1)
        self.assertEqual([cue.event for cue in self.cues],
                         ["object_recall_saved_food", "object_consuming_food"])
        self.assertEqual(self.consumed[0][2], ConsumptionOrigin.AUTONOMOUS)
        self.acknowledge()
        self.stamp = 1000
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "eat")
        self.coordinator.receive(PlaybackEvent(2, "eat", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "finish")
        self.assertEqual(self.cues[-1].event, "object_finished_food")
        self.acknowledge()
        self.assertEqual(self.done, [(self.item.instance_id, True)])
        self.assertEqual(self.memory.snapshot(), ())

    def test_returned_known_target_resumes_same_retrieval_without_identification(self):
        self.begin_retrieval()
        episode = self.coordinator.feedback_key.interaction_id
        self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.assertTrue(self.coordinator.target_taken(self.item.instance_id))
        self.acknowledge()
        self.coordinator.observe_held_offer(
            self.item.instance_id,
            decide_object_use(self.memory.get(self.item.instance_id), self.pet,
                              ObjectUseContext.OFFER),
        )
        self.assertEqual(self.coordinator.phase, "decide_offer")
        self.acknowledge()
        item = self.world.get(self.item.instance_id)
        self.world.return_user_held(item.instance_id, 110,
                                    expected_revision=item.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.acknowledge()
        self.coordinator.arrive()
        self.coordinator.receive(PlaybackEvent(2, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertEqual(self.coordinator.feedback_key.interaction_id, episode)
        self.assertNotIn("object_recognized", [cue.event for cue in self.cues])
        self.assertEqual(len(self.consumed), 1)
        self.assertEqual(self.consumed[0][2], ConsumptionOrigin.AUTONOMOUS)

    def test_returned_target_handover_retains_episode_and_actual_human_origin(self):
        self.begin_retrieval()
        episode = self.coordinator.feedback_key.interaction_id
        self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.coordinator.target_taken(self.item.instance_id)
        self.assertTrue(self.coordinator.offer_on_release(self.item.instance_id))
        self.assertEqual(self.coordinator.phase, "handover")
        self.assertEqual(self.coordinator.feedback_key.interaction_id, episode)
        self.assertEqual(self.consumed, [])
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertEqual(self.consumed[0][2], ConsumptionOrigin.HANDOVER)

    def test_cursor_assessment_shortens_resumed_investigation(self):
        self.memory.restore_snapshot(tuple(replace(item, assessed=False)
                                           for item in self.memory.snapshot()))
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "investigate",
        ))
        self.acknowledge()
        self.acknowledge()
        self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.coordinator.target_taken(self.item.instance_id)
        self.memory.mark_assessed(self.item.instance_id)
        self.acknowledge()
        item = self.world.get(self.item.instance_id)
        self.world.return_user_held(item.instance_id, 110,
                                    expected_revision=item.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.acknowledge()
        self.coordinator.arrive()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertNotIn("object_recognized", [cue.event for cue in self.cues])

    def test_actual_target_loss_releases_focus_to_bounded_subjective_search(self):
        self.begin_retrieval()
        self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.coordinator.target_taken(self.item.instance_id)
        self.coordinator.observe_target_state(None)
        self.assertEqual(self.coordinator.phase, "search")
        self.assertIsNone(self.coordinator.focus_record)
        # Losing visual tracking is not a local observation of an empty place.
        self.assertEqual(self.memory.snapshot()[0].place_status, "remembered")

    def test_drink_recall_matches_energy_and_only_claims_confirmed_deferral(self):
        self.memory.update((replace(self.seen, identity="energy_drink", kind="drink"),),
                           now=0)
        self.memory.mark_assessed(self.item.instance_id)
        goal = ObjectIntentions().choose(self.memory.snapshot(), self.pet, x=0, now=0)
        assert goal is not None
        self.coordinator.begin_goal(goal)
        self.assertEqual(self.cues[-1].event, "object_recall_drink")
        self.coordinator.interrupt(lambda: None)
        self.memory.note_placement(self.item.instance_id, x=100, height=0,
                                   now=0, deferred=True)
        self.coordinator.begin_goal(goal)
        self.assertEqual(self.cues[-1].event, "object_recall_saved_drink")

    def test_known_but_unassessed_item_decides_without_identifying_again(self):
        self.memory.restore_snapshot(tuple(replace(item, assessed=False,
                                                   disposition=None)
                                           for item in self.memory.snapshot()))
        self.coordinator.begin_goal(ObjectGoal(self.item.instance_id, "apple", "food",
                                               100, 0, 0, "consume"))
        self.assertEqual(self.cues[-1].event, "object_consider_known")
        self.acknowledge()
        self.coordinator.arrive()
        self.acknowledge()
        self.acknowledge()
        self.grasp()
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "decide")
        self.assertEqual(self.cues[-1].event, "object_want")
        self.assertTrue(self.memory.snapshot()[0].assessed)
        self.assertNotIn("object_recognized", [cue.event for cue in self.cues])
        self.assertEqual(self.consumed, [])
        self.acknowledge()
        self.assertEqual(len(self.consumed), 1)

    def test_changed_needs_after_grasp_lead_to_readable_decline_and_put_down(self):
        self.begin_retrieval()
        self.grasp()
        self.pet.satiety = 100
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "decide")
        self.assertEqual(self.cues[-1].event, "object_later")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "put_down")
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.assertEqual(self.memory.snapshot()[0].disposition, "deferred")
        self.assertEqual(self.consumed, [])

    def test_unknown_identity_cannot_be_supplied_by_a_forged_consumption_goal(self):
        self.memory.restore_snapshot(tuple(replace(
            item, identity=None, kind=None, assessed=False,
        ) for item in self.memory.snapshot()))
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "consume",
        ))
        self.acknowledge()
        self.acknowledge()
        self.coordinator.arrive()
        self.acknowledge()
        self.grasp()
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "inspect")
        self.stamp = 2
        self.acknowledge()
        self.acknowledge()
        self.assertEqual(self.cues[-1].event, "object_inspect")
        self.assertEqual(self.coordinator.phase, "inspect")
        self.assertEqual(self.consumed, [])
        self.assertFalse(self.memory.snapshot()[0].assessed)
        self.memory.update((ObjectObservation(
            self.item.instance_id, "apple", "food", 100, 70, False, 2,
        ),), now=2)
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "recognize")
        self.assertEqual(self.cues[-1].event, "object_recognized")

    def test_interrupted_retrieval_preserves_learning_but_not_deliberate_deferral(self):
        self.begin_retrieval()
        self.grasp()
        self.coordinator.interrupt(lambda: self.actions.append("game"))
        self.finish_pickup()
        self.assertEqual(self.actions, ["pick_up", "put_down"])
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.assertEqual(self.actions[-1], "game")
        self.assertTrue(self.memory.snapshot()[0].assessed)
        self.assertEqual(self.memory.snapshot()[0].disposition, "interrupted")
        self.assertEqual(self.consumed, [])

    def test_conflicting_observation_during_pickup_restores_full_inspection(self):
        self.begin_retrieval()
        self.grasp()
        self.memory.update((replace(self.seen, identity="energy_drink", kind="drink",
                                     resting=False),), now=0)
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "inspect")
        self.assertEqual(self.consumed, [])

    def test_assessed_handover_waits_for_acknowledgement_without_reinspection(self):
        item = self.world.create_held("energy_drink", WorldPosition(100, 80),
                                      ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(
            item.instance_id, "energy_drink", "drink", 100, 80, False, 0,
        ),), now=0)
        self.memory.mark_assessed(item.instance_id)
        self.assertTrue(self.coordinator.offer_on_release(item.instance_id))
        self.assertEqual(self.coordinator.phase, "handover")
        self.assertEqual(self.cues[-1].event, "object_handover")
        self.assertEqual(self.world.get(item.instance_id).state, ObjectState.PET_HELD)
        self.assertEqual(self.consumed, [])
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertEqual(self.consumed[0][2], ConsumptionOrigin.HANDOVER)
        self.assertEqual([cue.event for cue in self.cues], [
            "object_handover", "object_consuming_drink",
        ])

    def test_cancelled_assessed_handover_puts_down_and_ignores_old_receipt(self):
        item = self.world.create_held("apple", WorldPosition(100, 80),
                                      ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(
            item.instance_id, "apple", "food", 100, 80, False, 0,
        ),), now=0)
        self.memory.mark_assessed(item.instance_id)
        self.coordinator.offer_on_release(item.instance_id)
        key = self.coordinator.feedback_key
        self.coordinator.receive_feedback(FeedbackReceipt(key, False))
        self.assertEqual(self.coordinator.phase, "put_down")
        self.coordinator.receive_feedback(FeedbackReceipt(key, True))
        self.assertEqual(self.consumed, [])

    def test_retrieval_after_interrupted_handover_has_fresh_origin_and_action(self):
        item = self.world.create_held("apple", WorldPosition(100, 80),
                                      ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(
            item.instance_id, "apple", "food", 100, 80, False, 0,
        ),), now=0)
        self.memory.mark_assessed(item.instance_id)
        self.assertTrue(self.coordinator.offer_on_release(item.instance_id))
        first = self.coordinator.feedback_key.interaction_id
        resumed = []
        self.coordinator.interrupt(lambda: resumed.append("game"))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.assertEqual(resumed, ["game"])
        self.assertFalse(self.coordinator.active)
        self.assertIsNone(self.coordinator.memory_id)
        self.assertIsNone(self.coordinator.instance_id)
        self.assertEqual(self.coordinator.feedback_key.interaction_id, first)
        self.assertTrue(self.coordinator.begin_goal(ObjectGoal(
            item.instance_id, "apple", "food", 110, 0, 0,
        )))
        self.assertNotEqual(self.coordinator.feedback_key.interaction_id, first)
        self.acknowledge()
        self.coordinator.arrive()
        self.coordinator.receive(PlaybackEvent(3, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(3, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "eat")
        self.assertEqual(self.consumed, [
            (self.coordinator.feedback_key.interaction_id,
             item.instance_id, ConsumptionOrigin.AUTONOMOUS),
        ])
        self.assertEqual(resumed, ["game"])

    def test_confirmed_absence_searches_once_and_marks_only_the_checked_place(self):
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "consume",
        ))
        self.acknowledge()
        # A valid paired save may omit a terminal instance while memory is stale.
        self.world.restore_snapshot(replace(self.world.snapshot(), objects=()))
        self.memory.update((ObjectObservation(
            self.item.instance_id, "apple", "food", 120, 0, True, 1,
        ),), now=1)
        self.coordinator.start_search()
        self.coordinator.start_search()
        self.assertEqual(self.coordinator.phase, "search")
        self.assertEqual(self.coordinator.search_x, 120)
        self.assertEqual(self.memory.snapshot()[0].place_status, "missing")
        self.acknowledge()
        self.stamp = 2.1
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "missing")
        self.assertEqual([cue.event for cue in self.cues].count("object_missing"), 1)
        self.assertEqual(self.memory.snapshot()[0].place_status, "missing")
        self.acknowledge()
        self.assertEqual(self.done, [(self.item.instance_id, False)])
        self.assertEqual(self.consumed, [])

    def test_found_supply_ends_search_and_stale_search_receipt_cannot_restart_it(self):
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "consume",
        ))
        self.acknowledge()
        self.coordinator.start_search()
        old = self.coordinator.feedback_key
        found = self.world.place_resting("apple", 200, ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(
            found.instance_id, "apple", "food", 200, 0, True, 1,
        ),), now=1)
        self.coordinator.found(ObjectGoal(
            found.instance_id, "apple", "food", 200, 0, 1, "investigate",
        ))
        self.assertEqual(self.coordinator.phase, "found")
        self.assertEqual(self.cues[-1].record_id, found.instance_id)
        self.coordinator.receive_feedback(FeedbackReceipt(old, True))
        self.assertEqual(self.coordinator.phase, "found")
        self.acknowledge()
        self.assertEqual(self.coordinator.memory_id, found.instance_id)
        self.assertEqual(self.coordinator.phase, "notice")
        self.assertEqual(self.done, [])

    def test_new_search_episode_gets_its_own_dwell_and_feedback(self):
        goal = ObjectGoal(self.item.instance_id, "apple", "food", 100, 0, 0)
        self.coordinator.begin_goal(goal)
        self.acknowledge()
        self.coordinator.start_search()
        old = self.coordinator.feedback_key
        self.acknowledge()
        self.stamp = 1.9
        self.assertAlmostEqual(self.coordinator.search_progress, .95)
        self.coordinator.interrupt(lambda: None)
        self.coordinator.begin_goal(goal)
        self.acknowledge()
        self.coordinator.start_search()
        self.assertNotEqual(self.coordinator.feedback_key.interaction_id,
                            old.interaction_id)
        self.assertEqual(self.coordinator.search_progress, 0)
        self.stamp = 4
        self.coordinator.receive_feedback(FeedbackReceipt(old, True))
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "search")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "missing")
        self.acknowledge()
        self.assertEqual(self.done, [(self.item.instance_id, False)] * 2)
        self.assertEqual(self.consumed, [])

    def test_search_reads_keep_their_last_facts_until_a_fresh_search_begins(self):
        self.stamp = 10
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0,
        ))
        self.acknowledge()
        self.coordinator.start_search()
        self.stamp = 11
        self.coordinator.interrupt(lambda: None)
        self.assertFalse(self.coordinator.active)
        self.assertEqual(self.coordinator.search_x, 100)
        self.assertEqual(self.coordinator.search_progress, .5)
        found = self.world.place_resting("apple", 240, ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(
            found.instance_id, "apple", "food", 240, 0, True, 11,
        ),), now=11)
        self.coordinator.begin_goal(ObjectGoal(
            found.instance_id, "apple", "food", 240, 0, 11,
        ))
        self.assertEqual(self.coordinator.search_x, 240)
        self.assertEqual(self.coordinator.search_progress, .5)
        self.acknowledge()
        self.coordinator.start_search()
        self.assertEqual(self.coordinator.search_progress, 0)

    def test_cancelling_approach_does_not_claim_absence_or_erase_known_stock(self):
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "consume",
        ))
        self.acknowledge()
        self.coordinator.interrupt(lambda: None)
        self.assertEqual(self.coordinator.phase, "idle")
        self.assertEqual(self.memory.snapshot()[0].disposition, "deferred")
        self.assertNotIn("object_missing", [cue.event for cue in self.cues])
