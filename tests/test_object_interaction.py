"""Grasp is distinct from nutrition; interruption safely reverses ownership."""

import unittest
from unittest.mock import patch

from aiko_pet.application.object_awareness import held_type_conflicts_with_memory
from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.balance import BALANCE
from aiko_pet.pet.mind.object_decisions import ObjectUseDecision
from aiko_pet.pet.mind.object_intentions import ObjectGoal
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.moodlets import MoodletId
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
from tools.pet_test_support import set_test_pet_values


class ObjectInteractionTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        self.item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.actions = []
        self.consumed = []
        self.done = []
        self.cues = []
        self.delay_feedback = False
        self.cancel_reports_previous = False
        self.cancelled_feedback = []
        self.handovers = []
        self.stamp = 0
        self.pet = PetState(friendship=50)
        self.decision = ObjectUseDecision(True, "hungry")

        def feedback(cue):
            self.cues.append(cue)
            if not self.delay_feedback:
                self.coordinator.receive_feedback(FeedbackReceipt(cue.key, True))

        def play(clip):
            self.actions.append(clip)
            return len(self.actions)

        def cancel_feedback():
            if self.cancel_reports_previous and self.cues:
                receipt = FeedbackReceipt(self.cues[-1].key, False)
                self.cancelled_feedback.append(receipt)
                self.coordinator.receive_feedback(receipt)

        def consume(key, item_id, memory_id, origin):
            self.consumed.append((key, item_id, origin))
            item = self.world.get(item_id)
            self.world.consume(item_id, expected_revision=item.revision)
            self.memory.forget(item_id)
            return True

        self.memory = ObjectMemory()
        self.memory.update((ObjectObservation(
            self.item.instance_id, "apple", "food", 100, 0, True, 0,
        ),), now=0)
        self.coordinator = ObjectInteractionCoordinator(
            self.world, play=play, stop=lambda: None, select_item=lambda _item: None,
            consume=consume, can_acquire=lambda _item: True, ground_x=lambda _item: 100,
            hand_type_conflicts=lambda record, instance: (
                held_type_conflicts_with_memory(
                    self.memory.get(record), instance, self.world.snapshot(),
                )
            ),
            completed=lambda item, consumed: self.done.append((item, consumed)),
            memory=self.memory,
            resolve_instance=lambda token: token,
            record_for_instance=lambda token: token,
            decide=lambda _token, _origin: self.decision,
            feedback=feedback, cancel_feedback=cancel_feedback, now=lambda: self.stamp,
            inspection_seconds=0,
            experience=self.pet.experience_interaction,
            withholding_active=lambda: any(
                e.definition_id == MoodletId.WITHHELD
                for e in self.pet.moodlets.active),
            acknowledge_handover=lambda item, record: self.handovers.append(
                (item, record),
            ),
        )

    def test_unknown_personal_handover_is_acknowledged_once_after_identification(self):
        self.delay_feedback = True
        self.coordinator._inspection_seconds = 1
        self.decision = ObjectUseDecision(False, "not_needed")
        item = self.world.create_held("apple", WorldPosition(100, 50),
                                     ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(item.instance_id, None, None,
                                              100, 50, False, 0),), now=0)
        self.assertTrue(self.coordinator.offer_on_release(item.instance_id))
        self.assertEqual(self.handovers, [])
        self.acknowledge()
        self.memory.update((ObjectObservation(item.instance_id, "apple", "food",
                                              100, 50, False, 1),), now=1)
        self.stamp = 1
        self.coordinator.update()
        self.acknowledge()
        self.assertEqual(self.handovers, [(item.instance_id, item.instance_id)])
        self.acknowledge()
        self.coordinator.update()
        self.assertEqual(len(self.handovers), 1)

    def start_investigation(self):
        # Acknowledge only approach cues; retain each case's pickup cue timing.
        delayed = self.delay_feedback
        self.delay_feedback = False
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, None, None, 100, 0, 0, "investigate",
        ))
        self.delay_feedback = delayed
        self.coordinator.arrive()

    def test_acquisition_precedes_consumption_and_duplicates_are_ignored(self):
        self.start_investigation()
        grasp = PlaybackEvent(1, "pick_up", 3, ("attach_object",))
        self.coordinator.receive(grasp)
        self.coordinator.receive(grasp)
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.PET_HELD)
        self.assertEqual(self.consumed, [])
        done = PlaybackEvent(1, "pick_up", 7, finished=True)
        self.coordinator.receive(done)
        self.coordinator.receive(done)
        self.assertEqual(len(self.consumed), 1)

    def test_phase_change_invalidates_receipt_before_synchronous_cancellation(self):
        self.delay_feedback = True
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, None, None, 100, 0, 0, "investigate",
        ))
        notice = self.cues[-1]
        self.cancel_reports_previous = True
        self.acknowledge()
        self.assertEqual(self.cancelled_feedback, [FeedbackReceipt(notice.key, False)])
        self.assertEqual(self.coordinator.phase, "approach")
        self.assertNotEqual(self.coordinator.feedback_key, notice.key)
        self.assertEqual(self.coordinator.focus_record, self.item.instance_id)
        self.assertEqual(self.done, [])
        self.coordinator.arrive()
        self.assertEqual(self.actions, [])
        self.acknowledge()
        self.assertEqual(self.actions, ["pick_up"])
        self.assertEqual(self.coordinator.phase, "pick_up")

    def test_new_episode_ignores_old_receipts_and_playback_for_the_same_item(self):
        self.delay_feedback = True
        self.start_investigation()
        old = self.coordinator.feedback_key
        self.coordinator.interrupt(lambda: None)
        self.start_investigation()
        current = self.coordinator.feedback_key
        self.assertNotEqual(current.interaction_id, old.interaction_id)
        world, memory = self.world.snapshot(), self.memory.snapshot()
        for completed in (False, True):
            self.coordinator.receive_feedback(FeedbackReceipt(old, completed))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.feedback_key, current)
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), memory)
        self.assertEqual(self.consumed, [])
        self.coordinator.receive(PlaybackEvent(2, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "inspect")
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.PET_HELD)

    def test_old_auxiliary_receipt_cannot_release_a_new_episode_phase(self):
        self.delay_feedback = True
        goal = ObjectGoal(self.item.instance_id, None, None, 100, 0, 0, "investigate")
        self.coordinator.begin_goal(goal)
        self.coordinator.receive_feedback(FeedbackReceipt(self.cues[-1].key, True))
        self.coordinator.request_feedback("object_busy")
        self.coordinator.update()
        aside = self.cues[-1]
        self.assertNotEqual(aside.key.auxiliary_id, 0)
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "approach")
        self.assertFalse(self.coordinator.contact_feedback_active)
        self.coordinator.receive_feedback(FeedbackReceipt(aside.key, True))
        self.coordinator.arrive()
        self.assertEqual(self.coordinator.phase, "approach")
        self.assertEqual(self.actions, [])
        self.coordinator.interrupt(lambda: None)
        self.coordinator.begin_goal(goal)
        current = self.coordinator.feedback_key
        for completed in (False, True):
            self.coordinator.receive_feedback(FeedbackReceipt(aside.key, completed))
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "notice")
        self.assertEqual(self.coordinator.feedback_key, current)
        self.assertEqual(self.cues[-1].event, "object_notice")
        self.assertEqual(self.actions, [])
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "approach")

    def test_contact_cooldown_survives_an_episode_restart(self):
        goal = ObjectGoal(self.item.instance_id, None, None, 100, 0, 0, "investigate")
        self.coordinator.begin_goal(goal)
        first = self.coordinator.feedback_key.interaction_id
        self.assertTrue(self.coordinator.acknowledge_contact())
        self.coordinator.update()
        self.assertEqual(self.cues[-1].event, "object_busy")
        self.coordinator.interrupt(lambda: None)
        self.coordinator.begin_goal(goal)
        self.assertNotEqual(self.coordinator.feedback_key.interaction_id, first)
        self.assertTrue(self.coordinator.acknowledge_contact())
        self.coordinator.update()
        self.assertEqual([cue.event for cue in self.cues].count("object_busy"), 1)
        self.stamp = BALANCE.number("object_behavior", "contact_feedback_seconds")
        self.assertTrue(self.coordinator.acknowledge_contact())
        self.coordinator.update()
        self.assertEqual([cue.event for cue in self.cues].count("object_busy"), 2)
        self.assertEqual(self.actions, [])

    def test_return_request_receipt_cannot_acknowledge_returned_item_phase(self):
        self.delay_feedback = True
        self.start_investigation()
        taken = self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.assertTrue(self.coordinator.target_taken(self.item.instance_id))
        taken_cue = self.cues[-1]
        self.assertEqual(taken_cue.event, "object_taken")
        self.acknowledge()
        self.stamp = BALANCE.number("object_withholding", "request_interval_seconds")
        self.coordinator.observe_target_state(ObjectState.USER_HELD)
        self.coordinator.update()
        request = self.cues[-1]
        self.assertEqual(request.event, "object_request_return")
        self.assertNotEqual(request.key, taken_cue.key)
        self.assertFalse(self.coordinator.contact_feedback_active)
        self.world.return_user_held(taken.instance_id, 100,
                                    expected_revision=taken.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "await_return")
        self.assertEqual(self.actions, ["pick_up"])
        self.coordinator.receive_feedback(FeedbackReceipt(request.key, True))
        self.assertEqual(self.coordinator.phase, "await_return")
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.assertEqual(self.cues[-1].event, "object_returned")
        returned_key = self.cues[-1].key
        for completed in (False, True):
            self.coordinator.receive_feedback(FeedbackReceipt(request.key, completed))
        self.coordinator.arrive()
        self.assertEqual(self.coordinator.phase, "approach")
        self.assertEqual(self.coordinator.feedback_key, returned_key)
        self.assertEqual(self.actions, ["pick_up"])
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.assertEqual(self.actions, ["pick_up", "pick_up"])
        self.assertEqual(self.consumed, [])

    def test_observed_take_invalidates_queued_grasp_without_losing_episode(self):
        self.start_investigation()
        key = self.coordinator.feedback_key.interaction_id
        taken = self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.assertTrue(self.coordinator.target_taken(self.item.instance_id))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.assertEqual(self.world.get(taken.instance_id).state, ObjectState.USER_HELD)
        self.assertEqual(self.coordinator.phase, "await_return")
        self.assertEqual(self.coordinator.feedback_key.interaction_id, key)
        self.assertEqual(self.done, [])
        self.assertEqual(self.consumed, [])

    def test_take_notification_does_not_interrupt_pet_held_custody(self):
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        # Attachment precedes clip completion: the phase still admits take
        # notifications, so custody itself must reject this late notification.
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.PET_HELD)
        episode = self.coordinator.feedback_key
        world, memory = self.world.snapshot(), self.memory.snapshot()
        self.assertFalse(self.coordinator.target_taken(self.item.instance_id))
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.assertEqual(self.coordinator.feedback_key, episode)
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), memory)
        self.assertEqual(self.actions, ["pick_up"])
        self.assertEqual(self.consumed, [])
        self.assertEqual(self.done, [])

    def test_observed_return_requires_a_fresh_arrival_after_an_earlier_approach(self):
        self.start_investigation()
        episode = self.coordinator.feedback_key.interaction_id
        taken = self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.assertTrue(self.coordinator.target_taken(self.item.instance_id))
        self.world.return_user_held(taken.instance_id, 110,
                                    expected_revision=taken.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.coordinator.update()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "approach")
        self.assertEqual(self.coordinator.feedback_key.interaction_id, episode)
        self.assertEqual(self.actions, ["pick_up"])
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.RESTING)
        self.coordinator.arrive()
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.assertEqual(self.actions, ["pick_up", "pick_up"])
        self.assertEqual(self.consumed, [])

    def test_pickup_cue_cannot_replace_clip_completion_or_next_phase_feedback(self):
        self.delay_feedback = True
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.assertEqual(self.consumed, [])
        finished = PlaybackEvent(1, "pick_up", 7, finished=True)
        self.coordinator.receive(finished)
        self.assertEqual(self.coordinator.phase, "inspect")
        current = self.coordinator.feedback_key
        self.coordinator.receive(finished)
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "inspect")
        self.assertEqual(self.coordinator.feedback_key, current)
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "recognize")
        self.assertEqual(self.consumed, [])

    def test_confirmed_detach_records_own_placement_before_clip_finishes(self):
        self.delay_feedback = True
        self.decision = ObjectUseDecision(False, "not_needed")
        self.start_investigation()
        self.acknowledge()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.assertFalse(self.memory.snapshot()[0].resting)
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "recognize")
        self.assertFalse(self.memory.snapshot()[0].assessed)
        self.acknowledge()
        self.assertTrue(self.memory.snapshot()[0].assessed)
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "put_down")
        self.assertIsNone(self.memory.snapshot()[0].disposition)
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        known = self.memory.snapshot()[0]
        self.assertEqual((known.resting, known.disposition), (True, "deferred"))
        self.assertEqual(self.coordinator.phase, "put_down")
        self.assertEqual(self.done, [])

    def test_failed_placement_rolls_back_and_same_event_can_retry(self):
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.interrupt(lambda: None)
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        world, memory = self.world.snapshot(), self.memory.snapshot()
        original = self.memory.note_placement

        def broken(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("injected placement failure")

        event = PlaybackEvent(2, "put_down", 2, ("detach_object",))
        with patch.object(self.memory, "note_placement", side_effect=broken):
            with self.assertRaises(RuntimeError):
                self.coordinator.receive(event)
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), memory)
        self.coordinator.receive(event)
        self.assertEqual(self.memory.snapshot()[0].disposition, "interrupted")
        self.assertFalse(self.memory.snapshot()[0].assessed)

    def test_failed_handover_restores_both_owners_before_retry(self):
        held = self.world.create_held("apple", WorldPosition(100, 50),
                                      ObjectFootprint(8, 8))
        self.memory.update((ObjectObservation(
            held.instance_id, "apple", "food", 100, 50, False, 0,
        ),), now=0)
        self.stamp = 1
        self.delay_feedback = True
        before_world, before_memory = self.world.snapshot(), self.memory.snapshot()
        original = self.memory.note_acquired

        def broken(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("injected handover failure")

        with patch.object(self.memory, "note_acquired", side_effect=broken):
            with self.assertRaises(RuntimeError):
                self.coordinator.offer_on_release(held.instance_id)
        self.assertEqual(self.world.snapshot(), before_world)
        self.assertEqual(self.memory.snapshot(), before_memory)
        self.assertFalse(self.coordinator.active)
        self.assertTrue(self.coordinator.offer_on_release(held.instance_id))
        self.assertEqual(self.world.get(held.instance_id).state, ObjectState.PET_HELD)
        self.assertEqual(self.coordinator.phase, "handover")
        self.assertEqual(self.cues[-1].event, "object_handover")

    def test_failed_grasp_rolls_back_world_and_memory_and_can_retry(self):
        self.start_investigation()
        world, memory = self.world.snapshot(), self.memory.snapshot()
        original = self.memory.note_acquired

        def broken(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("injected acquisition failure")

        event = PlaybackEvent(1, "pick_up", 3, ("attach_object",))
        with patch.object(self.memory, "note_acquired", side_effect=broken):
            with self.assertRaises(RuntimeError):
                self.coordinator.receive(event)
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), memory)
        self.coordinator.receive(event)
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.PET_HELD)

    def test_interruption_after_grasp_puts_down_before_user_action(self):
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.interrupt(lambda: self.actions.append("game"))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.actions, ["pick_up", "put_down"])
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.assertEqual(self.actions[-1], "game")
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.RESTING)
        self.assertEqual(self.consumed, [])

    def test_repeated_effect_in_different_envelope_cannot_grasp_or_release_twice(self):
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 4, ("attach_object",)))
        self.assertEqual(self.coordinator.phase, "pick_up")
        self.coordinator.interrupt(lambda: self.actions.append("sleep"))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 1, ("detach_object",)))
        self.coordinator.interrupt(lambda: self.actions.append("game"))
        self.assertEqual(self.coordinator.phase, "put_down")
        self.assertNotIn("game", self.actions)
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.assertEqual(self.actions[-1], "game")
        self.assertNotIn("sleep", self.actions)
        self.assertEqual(self.consumed, [])

    def test_interrupting_committed_eating_preserves_consumed_completion(self):
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.coordinator.interrupt(lambda: self.actions.append("talk"))
        self.assertEqual(self.done, [(self.item.instance_id, True)])
        self.assertEqual(self.actions[-1], "talk")
        self.assertEqual(len(self.consumed), 1)

    def test_cancelled_finish_feedback_keeps_consumption_and_completes_once(self):
        self.start_investigation()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "eat")
        self.delay_feedback = True
        finished = PlaybackEvent(2, "eat", 7, finished=True)
        self.coordinator.receive(finished)
        self.assertEqual(self.coordinator.phase, "finish")
        key = self.coordinator.feedback_key
        self.coordinator.receive_feedback(FeedbackReceipt(key, False))
        self.coordinator.update()
        self.coordinator.receive_feedback(FeedbackReceipt(key, True))
        self.coordinator.receive(finished)
        self.coordinator.update()
        self.assertFalse(self.coordinator.active)
        self.assertEqual(self.done, [(self.item.instance_id, True)])
        self.assertEqual(len(self.consumed), 1)
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.CONSUMED)
        self.assertEqual(self.actions, ["pick_up", "eat"])

    def acknowledge(self):
        self.coordinator.receive_feedback(FeedbackReceipt(self.cues[-1].key, True))
        self.coordinator.update()

    def test_investigation_requires_actual_arrival_and_phase_receipts(self):
        self.delay_feedback = True
        goal = ObjectGoal(self.item.instance_id, None, None, 100, 0, 0, "investigate")
        self.coordinator.begin_goal(goal)
        notice = self.cues[-1]
        self.coordinator.arrive()
        self.assertEqual(self.coordinator.phase, "notice")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "approach")
        self.coordinator.arrive()
        self.coordinator.receive_feedback(FeedbackReceipt(notice.key, True))
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "approach")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "pick_up")

    def test_inspection_and_defer_never_consume_and_wait_for_readable_decision(self):
        self.delay_feedback = True
        self.decision = ObjectUseDecision(False, "not_needed")
        self.coordinator._inspection_seconds = 1
        self.start_investigation()
        self.acknowledge()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(self.coordinator.phase, "inspect")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "inspect")
        self.stamp = 1
        self.coordinator.update()
        self.assertEqual(self.coordinator.phase, "recognize")
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "decide")
        self.assertEqual(self.consumed, [])
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "put_down")
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.assertEqual(self.done, [])
        self.acknowledge()
        self.assertEqual(self.done, [(self.item.instance_id, False)])
        self.assertEqual(self.consumed, [])

    def test_pending_preinspection_loss_waits_for_readable_recognition(self):
        self.memory.update((ObjectObservation(
            "missing", "energy_drink", "drink", 200, 0, True, 0,
        ),), now=0)
        missing = self.memory.get("missing")
        learned = self.memory.get(self.item.instance_id)
        assert missing is not None and learned is not None
        # This immutable loss was confirmed at the old empty place, before the
        # hand action, but reaction was deferred. No environment is seen in hand.
        self.world.move_resting(self.item.instance_id, 300, expected_revision=0)
        self.memory.mark_missing(learned.token)
        self.delay_feedback = True
        self.coordinator.notice_absence(missing)
        self.acknowledge()
        self.acknowledge()
        self.start_investigation()
        self.acknowledge()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "recognize")
        receipt = self.coordinator.feedback_key
        self.assertTrue(self.coordinator.notice_absence(learned))
        self.coordinator.update()
        self.assertEqual(self.coordinator.feedback_key, receipt)
        self.assertNotIn("object_found", [cue.event for cue in self.cues])
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "found")
        self.assertEqual(self.cues[-1].record_id, self.item.instance_id)
        self.assertEqual([cue.event for cue in self.cues].count("object_found"), 1)
        self.assertEqual(self.consumed, [])
        self.assertEqual(self.world.get(self.item.instance_id).state,
                         ObjectState.PET_HELD)
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "put_down")
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.acknowledge()
        self.assertEqual(self.coordinator.phase, "search")
        self.assertEqual(self.coordinator.memory_id, "missing")
        self.assertEqual(self.consumed, [])

    def test_cancelled_inspection_recovers_custody_and_ignores_stale_receipt(self):
        self.delay_feedback = True
        self.start_investigation()
        self.acknowledge()
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        cancelled = self.cues[-1].key
        self.coordinator.receive_feedback(FeedbackReceipt(cancelled, False))
        self.assertEqual(self.coordinator.phase, "put_down")
        self.coordinator.receive_feedback(FeedbackReceipt(cancelled, True))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 2, ("detach_object",)))
        self.coordinator.receive(PlaybackEvent(2, "put_down", 0, finished=True))
        self.assertEqual(self.coordinator.phase, "idle")
        self.assertEqual(self.consumed, [])

    def test_withholding_moodlet_uses_irritation_and_thirty_observed_seconds(self):
        self.start_investigation()
        taken = self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.coordinator.target_taken(self.item.instance_id)
        self.assertFalse(self.pet.moodlets.active)
        for stamp, level in ((10, 0), (20, 1), (30, 1), (40, 1), (50, 2),
                             (60, 2), (70, 2), (80, 3)):
            self.stamp = stamp
            set_test_pet_values(self.pet, lived_seconds=stamp)
            self.coordinator.observe_target_state(ObjectState.USER_HELD)
            self.coordinator.update()
            self.assertEqual(self.pet.moodlets.active[0].level
                             if self.pet.moodlets.active else 0, level)
        self.assertEqual(self.pet.friendship, 50)  # No second direct penalty.
        self.assertTrue(self.pet.moodlets.active[0].decay_paused)
        self.world.return_user_held(taken.instance_id, 110,
                                    expected_revision=taken.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.assertFalse(self.pet.moodlets.active[0].decay_paused)
        self.assertEqual(self.pet.moodlets.active[0].level, 3)

    def test_unwanted_object_has_no_withholding_emotion_and_retake_counts_once(self):
        self.start_investigation()
        taken = self.world.take_resting(self.item.instance_id, expected_revision=0)
        self.coordinator.target_taken(self.item.instance_id)
        self.stamp = 20
        self.decision = ObjectUseDecision(False, "not_needed")
        self.coordinator.observe_target_state(ObjectState.USER_HELD)
        self.assertFalse(self.pet.moodlets.active)
        self.world.return_user_held(taken.instance_id, 100,
                                    expected_revision=taken.revision)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.decision = ObjectUseDecision(True, "hungry")
        item = self.world.get(taken.instance_id)
        self.world.take_resting(item.instance_id, expected_revision=item.revision)
        self.coordinator.target_taken(item.instance_id)
        self.stamp = 40
        self.coordinator.observe_target_state(ObjectState.USER_HELD)
        self.coordinator.update()
        self.assertEqual(self.pet.moodlets.active[0].level, 1)
        self.coordinator.observe_target_state(ObjectState.RESTING)
        self.stamp = 41
        self.coordinator.target_taken(item.instance_id)
        self.assertEqual(self.pet.moodlets.active[0].level, 2)
        self.stamp = 61
        self.coordinator.observe_target_state(ObjectState.USER_HELD)
        self.assertEqual(self.pet.moodlets.active[0].level, 2)
