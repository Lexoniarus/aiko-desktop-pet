"""Known stock bypasses repeated inquiry while custody/use gates remain intact."""

import unittest
from dataclasses import replace

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.mind.object_decisions import decide_object_use
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
            now=lambda: self.stamp, inspection_seconds=1,
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

    def test_recognized_but_unexamined_item_cannot_take_shortcut_from_forged_goal(self):
        self.memory.restore_snapshot(tuple(replace(item, assessed=False,
                                                   disposition=None)
                                           for item in self.memory.snapshot()))
        self.coordinator.begin_goal(ObjectGoal(self.item.instance_id, "apple", "food",
                                               100, 0, 0, "consume"))
        self.assertEqual(self.cues[-1].event, "object_notice")
        self.acknowledge()
        self.coordinator.arrive()
        self.acknowledge()
        self.acknowledge()
        self.grasp()
        self.finish_pickup()
        self.assertEqual(self.coordinator.phase, "inspect")
        self.assertEqual(self.cues[-1].event, "object_inspect")
        self.assertEqual(self.consumed, [])

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

    def test_confirmed_absence_announces_once_and_clears_only_the_missing_memory(self):
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "consume",
        ))
        self.acknowledge()
        # A valid paired save may omit a terminal instance while memory is stale.
        self.world.restore_snapshot(replace(self.world.snapshot(), objects=()))
        self.coordinator.missing()
        self.coordinator.missing()
        self.assertEqual(self.coordinator.phase, "missing")
        self.assertEqual([cue.event for cue in self.cues].count("object_missing"), 1)
        self.assertEqual(self.memory.snapshot(), ())
        self.acknowledge()
        self.assertEqual(self.done, [(self.item.instance_id, False)])
        self.assertEqual(self.consumed, [])

    def test_cancelling_approach_does_not_claim_absence_or_erase_known_stock(self):
        self.coordinator.begin_goal(ObjectGoal(
            self.item.instance_id, "apple", "food", 100, 0, 0, "consume",
        ))
        self.acknowledge()
        self.coordinator.interrupt(lambda: None)
        self.assertEqual(self.coordinator.phase, "idle")
        self.assertEqual(self.memory.snapshot()[0].disposition, "deferred")
        self.assertNotIn("object_missing", [cue.event for cue in self.cues])
