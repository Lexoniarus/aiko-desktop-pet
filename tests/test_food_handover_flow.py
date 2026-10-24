"""Headless custody, real identification, desired intake and saved pending gifts."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from test_wish_assignment import wish

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.object_consumption import ObjectConsumption
from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.food_handover import HandoverStatus
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.object_decisions import decide_object_use
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishArea, WishId, WishState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.pet_test_support import require_test_value

WALL = 1800000000


class FoodFlow:
    def __init__(self, key=WishId.FOOD, *, known=True, actual="apple"):
        self.actual = actual
        self.stamp = 0
        self.pet = PetState(
            updated_at=WALL,
            lived_seconds=100,
            satiety=100,
            friendship=50,
            wishes=WishState(
                2, (wish(key, "apple"),), ((WishArea.FOOD, 0),), refresh_at=600
            ),
        )
        self.pet.advance(WALL, elapsed_seconds=0)
        self.world = WorldState(
            WorldSurface(800, 600),
            (
                ObjectDefinition(
                    actual,
                    actual,
                    actual,
                    frozenset((ObjectInteraction.EAT,)),
                ),
            ),
        )
        self.item = self.world.create_held(
            actual, WorldPosition(100, 50), ObjectFootprint(8, 8)
        )
        self.memory = ObjectMemory()
        self.observe(known)
        self.use = ObjectConsumption(
            self.pet,
            make_aiko_mind(started_at=0),
            AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: self.stamp),
            memory=self.memory,
        )
        self.clips, self.cues = [], []

        def play(clip):
            self.clips.append(clip)
            return len(self.clips)

        self.coordinator = ObjectInteractionCoordinator(
            self.world,
            play=play,
            stop=lambda: None,
            select_item=lambda _id: None,
            consume=lambda key, item, record, origin: (
                self.use.commit(
                    self.world,
                    key,
                    item,
                    origin,
                    self.inputs(),
                    memory_id=record,
                ).accepted
            ),
            resolve_instance=lambda record: self.item.instance_id,
            record_for_instance=lambda item: self.item.instance_id,
            can_acquire=lambda item: True,
            ground_x=lambda item: 100,
            hand_type_conflicts=lambda *_: False,
            completed=lambda *_: None,
            memory=self.memory,
            feedback=self.cues.append,
            cancel_feedback=lambda: None,
            decide=lambda record, context: decide_object_use(
                self.memory.get(record),
                self.pet,
                context,
            ),
            now=lambda: self.stamp,
            inspection_seconds=0,
            begin_handover=lambda item, record: self.use.begin_handover(
                self.world,
                item,
                self.inputs(),
                memory_id=record,
            ),
            finish_handover=lambda item: self.use.finish_handover(self.world, item),
            acknowledge_handover=lambda item, record: self.use.acknowledge_handover(
                self.world,
                item,
                self.inputs(),
                memory_id=record,
            ),
        )

    def inputs(self):
        return SessionInputs(
            WALL + self.stamp, self.stamp, False, None, False, False, None
        )

    def observe(self, known):
        self.memory.update(
            (
                ObjectObservation(
                    self.item.instance_id,
                    self.actual if known else None,
                    "food" if known else None,
                    100,
                    50,
                    False,
                    self.stamp,
                ),
            ),
            now=self.stamp,
        )
        if known:
            self.memory.restore_snapshot(
                tuple(
                    replace(k, instance_id=self.item.instance_id)
                    for k in self.memory.snapshot()
                )
            )

    def admit(self):
        return self.coordinator.offer_on_release(self.item.instance_id)

    def acknowledge(self):
        self.coordinator.receive_feedback(FeedbackReceipt(self.cues[-1].key, True))
        self.coordinator.update()


class FoodHandoverFlowTests(unittest.TestCase):
    def test_cursor_presentation_is_neither_handover_nor_nutrition(self):
        flow = FoodFlow()
        before = flow.pet.capture_checkpoint()
        flow.use.acknowledge_handover(
            flow.world,
            flow.item.instance_id,
            flow.inputs(),
            memory_id=flow.item.instance_id,
        )
        self.assertEqual(flow.pet.capture_checkpoint(), before)
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.USER_HELD
        )

    def test_desired_full_need_gift_is_consumed_once_without_a_second_wish_award(self):
        flow = FoodFlow()
        self.assertTrue(flow.admit())
        episode = flow.pet.moodlets.active[0]
        self.assertFalse(flow.pet.food.recent_food_ids)
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.PET_HELD
        )
        next_wish = wish(WishId.FOOD, "apple", instance=2, at=100)
        flow.pet.restore_checkpoint(
            replace(
                flow.pet.capture_checkpoint(),
                wishes=replace(
                    flow.pet.wishes,
                    active=(next_wish,),
                    next_instance_id=3,
                    last_created_by_area=((WishArea.FOOD, 100),),
                ),
            )
        )
        flow.acknowledge()
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.CONSUMED
        )
        self.assertEqual(flow.pet.food.recent_food_ids, ("apple",))
        self.assertEqual(flow.pet.satiety, 100)
        self.assertEqual(flow.pet.wishes.active, (next_wish,))
        self.assertEqual(flow.pet.moodlets.active[0], episode)
        self.assertFalse(flow.pet.wishes.food_handovers)
        self.assertEqual(flow.pet.friendship, 50)

    def test_unknown_gift_retains_original_wish_until_actual_hand_identification(self):
        flow = FoodFlow(known=False)
        flow.admit()
        self.assertFalse(flow.pet.moodlets.active)
        self.assertEqual(
            flow.pet.wishes.food_handovers[0].status, HandoverStatus.PENDING
        )
        flow.acknowledge()
        flow.pet.dismiss_wish(1)
        flow.stamp = 1
        flow.observe(True)
        flow.coordinator.update()
        cause = flow.pet.moodlets.active[0].causes[0]
        self.assertEqual(require_test_value(cause.wish).instance_id, 1)
        self.assertEqual((cause.handed_over_at, cause.occurred_at), (100, 101))
        flow.acknowledge()  # Recognition, then actual use decision.
        flow.acknowledge()  # Wanted-food cue, then actual consumption start.
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.CONSUMED
        )
        self.assertEqual(flow.pet.food.recent_food_ids, ("apple",))

    def test_unwanted_gift_is_put_down_without_eating_and_keeps_negative_moodlet(self):
        flow = FoodFlow(WishId.AVOID_FOOD)
        flow.admit()
        self.assertEqual(
            flow.pet.moodlets.active[0].definition_id, MoodletId.FOOD_WISH_DISREGARDED
        )
        flow.acknowledge()  # Handover -> separate use refusal.
        flow.acknowledge()  # Refusal -> put-down animation.
        flow.coordinator.receive(
            PlaybackEvent(
                len(flow.clips), "put_down", 2, ("detach_object",), finished=True
            )
        )
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.RESTING
        )
        self.assertFalse(flow.pet.food.recent_food_ids)
        self.assertNotIn("eat", flow.clips)
        flow.acknowledge()  # Actual put-down feedback finishes this transfer.
        self.assertFalse(flow.pet.wishes.food_handovers)
        self.assertEqual(flow.pet.moodlets.active[0].level, 1)

    def test_failed_transfer_restores_world_memory_and_pet_before_custody(self):
        flow = FoodFlow()
        physical, cognitive = flow.world.snapshot(), flow.memory.snapshot()
        before = flow.pet.capture_checkpoint()
        with patch.object(
            flow.pet,
            "recognize_food_handover",
            side_effect=RuntimeError("injected recognition failure"),
        ):
            with self.assertRaises(RuntimeError):
                flow.admit()
        self.assertEqual(flow.world.snapshot(), physical)
        self.assertEqual(flow.memory.snapshot(), cognitive)
        self.assertEqual(flow.pet.capture_checkpoint(), before)

    def test_alternative_food_at_full_satiety_can_fulfill_without_being_eaten(self):
        flow = FoodFlow(WishId.AVOID_FOOD, actual="cookie")
        flow.admit()
        episode = flow.pet.moodlets.active[0]
        self.assertEqual(episode.definition_id, MoodletId.FOOD_FULFILLED)
        self.assertEqual(episode.causes[0].target_id, "cookie")
        flow.acknowledge()
        flow.acknowledge()
        flow.coordinator.receive(
            PlaybackEvent(
                len(flow.clips),
                "put_down",
                2,
                ("detach_object",),
                finished=True,
            )
        )
        flow.acknowledge()
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.RESTING
        )
        self.assertFalse(flow.pet.food.recent_food_ids)
        self.assertEqual(flow.pet.moodlets.active[0], episode)
        self.assertFalse(flow.pet.wishes.food_handovers)

    def test_failed_intake_keeps_gift_and_permission_until_retry(self):
        flow = FoodFlow()
        flow.admit()
        before, physical = flow.pet.capture_checkpoint(), flow.world.snapshot()
        with patch.object(flow.world, "consume", side_effect=RuntimeError("injected")):
            with self.assertRaises(RuntimeError):
                flow.acknowledge()
        self.assertEqual(flow.pet.capture_checkpoint(), before)
        self.assertEqual(flow.world.snapshot(), physical)
        flow.coordinator.update()
        self.assertEqual(
            flow.world.get(flow.item.instance_id).state, ObjectState.CONSUMED
        )
        self.assertEqual(flow.pet.moodlets.active[0], before.moodlets.active[0])

    def test_safe_restore_keeps_unknown_gift_and_user_withdrawal_cancels_it(self):
        flow = FoodFlow(known=False)
        flow.admit()
        with tempfile.TemporaryDirectory() as folder:
            store = StateStore(Path(folder) / "state.json")
            store.save(
                flow.pet,
                PetSettings(auto_routine=False),
                world=flow.world.snapshot(),
                object_memory=flow.memory.export(now=0),
                world_recovery_x=100,
            )
            restored = PetSessionRestorer(store, wall_time=lambda: WALL).restore()
        world = WorldState(
            require_test_value(restored.world).surface,
            require_test_value(restored.world).definitions,
        )
        world.restore_snapshot(require_test_value(restored.world))
        ObjectConsumption.reconcile_handovers(restored.state, world)
        self.assertFalse(restored.state.moodlets.active)
        receipt = restored.state.wishes.food_handovers[0]
        self.assertEqual(receipt.status, HandoverStatus.PENDING)
        item = world.get(flow.item.instance_id)
        self.assertEqual(item.state, ObjectState.RESTING)
        world.take_resting(item.instance_id, expected_revision=item.revision)
        ObjectConsumption.reconcile_handovers(restored.state, world)
        self.assertEqual(
            restored.state.wishes.food_handovers[0].status, HandoverStatus.CANCELLED
        )
        restored.state.recognize_food_handover(receipt.handover_id, "apple")
        self.assertFalse(restored.state.moodlets.active)
