"""Joined pet/World effects survive duplicates and recover partial failures."""

import unittest
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.object_consumption import ObjectConsumption
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectConsumptionTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.item = self.world.collect_resting(item.instance_id, expected_revision=0)
        self.pet = PetState(satiety=50)
        self.mind = make_aiko_mind(started_at=0)
        self.memory = ObjectMemory()
        self.memory.update((ObjectObservation(
            self.item.instance_id, "apple", "food", 100, 0, False, 0,
        ),), now=0)
        self.use_case = ObjectConsumption(
            self.pet, self.mind, AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0), memory=self.memory,
        )
        self.inputs = SessionInputs(1_800_000_000, 1, False, None, False, False, None)

    def consume(self):
        return self.use_case.commit(self.world, "one", self.item.instance_id,
                                      ConsumptionOrigin.AUTONOMOUS, self.inputs,
                                      memory_id=self.item.instance_id)

    def test_identical_replay_returns_receipt_without_another_effect(self):
        first = self.consume()
        pet, world = deepcopy(self.pet), self.world.snapshot()
        self.assertTrue(first.accepted)
        self.assertEqual(self.consume(), first)
        self.assertEqual(self.pet, pet)
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), ())

    def test_autonomous_consumption_does_not_record_human_contact_in_the_mind(self):
        before = self.mind.last_contact
        self.assertTrue(self.consume().accepted)
        self.assertEqual(self.mind.last_contact, before)

    def test_place_hypothesis_cannot_consume_a_different_catalog_item(self):
        self.memory.update((ObjectObservation(
            self.item.instance_id, "onigiri", "food", 100, 0, False, 1,
        ),), now=1)
        world, memory = self.world.snapshot(), self.memory.snapshot()
        self.assertFalse(self.consume().accepted)
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), memory)
        self.assertEqual(self.pet.satiety, 50)

    def test_rejected_handover_does_not_record_contact_in_mind(self):
        self.memory.update((ObjectObservation(
            self.item.instance_id, "cookie", "food", 100, 0, False, 1,
        ),), now=1)
        before = self.mind.last_contact
        outcome = self.use_case.commit(
            self.world, "rejected", self.item.instance_id,
            ConsumptionOrigin.HANDOVER, self.inputs,
            memory_id=self.item.instance_id,
        )
        self.assertFalse(outcome.accepted)
        self.assertEqual(self.mind.last_contact, before)
        self.assertEqual(self.mind._last_care_action, "")

    def test_accepted_handover_updates_contact_once_after_commit(self):
        before = self.mind.last_contact
        outcome = self.use_case.commit(
            self.world, "handed", self.item.instance_id,
            ConsumptionOrigin.HANDOVER, self.inputs,
            memory_id=self.item.instance_id,
        )
        self.assertTrue(outcome.accepted)
        self.assertNotEqual(self.mind.last_contact, before)
        self.assertEqual(self.mind.last_contact, self.inputs.monotonic_time)
        replay = self.use_case.commit(
            self.world, "handed", self.item.instance_id,
            ConsumptionOrigin.HANDOVER,
            SessionInputs(self.inputs.wall_time + 10, 11, False, None,
                          False, False, None),
            memory_id=self.item.instance_id,
        )
        self.assertEqual(replay, outcome)
        self.assertEqual(self.mind.last_contact, self.inputs.monotonic_time)

    def test_failure_after_memory_mutation_restores_all_three_owners(self):
        world, memory = self.world.snapshot(), self.memory.snapshot()
        original = self.memory.forget

        def broken(token):
            original(token)
            raise RuntimeError("injected memory failure")

        with patch.object(self.memory, "forget", side_effect=broken):
            with self.assertRaises(RuntimeError):
                self.consume()
        self.assertEqual(self.world.snapshot(), world)
        self.assertEqual(self.memory.snapshot(), memory)
        self.assertEqual(self.pet.satiety, 50)
        self.assertTrue(self.consume().accepted)
        self.assertEqual(self.memory.snapshot(), ())

    def test_failed_handover_recovers_all_pet_values_and_identity(self):
        self.pet.advance(self.inputs.wall_time, elapsed_seconds=0)
        self.pet.restore_checkpoint(replace(
            self.pet.capture_checkpoint(),
            moodlets=MoodletState(0, 2, (
                MoodletEpisode(1, MoodletId.POKING, 2, 0, 0, 900, (2,)),
            )),
            wishes=WishState(2, (
                ActiveWish(1, WishId.FOOD, "apple", 0, 14400),
            ), ((WishArea.FOOD, 0),)),
        ))
        original_pet = self.pet
        before = self.pet.capture_checkpoint()
        world_before = self.world.snapshot()
        memory_before = self.memory.snapshot()
        contact_before = self.mind.last_contact
        forget = self.memory.forget

        def fail_after_forget(token):
            forget(token)
            self.pet.restore_checkpoint(replace(
                self.pet.capture_checkpoint(),
                moodlets=replace(self.pet.moodlets, active=()),
                wishes=replace(self.pet.wishes, active=()),
            ))
            raise RuntimeError("injected history rollback")

        with patch.object(self.memory, "forget", side_effect=fail_after_forget):
            with self.assertRaises(RuntimeError):
                self.use_case.commit(
                    self.world, "handover", self.item.instance_id,
                    ConsumptionOrigin.HANDOVER, self.inputs,
                    memory_id=self.item.instance_id,
                )
        self.assertIs(self.pet, original_pet)
        self.assertEqual(self.pet.capture_checkpoint(), before)
        self.assertEqual(self.world.snapshot(), world_before)
        self.assertEqual(self.memory.snapshot(), memory_before)
        self.assertEqual(self.mind.last_contact, contact_before)
        self.assertTrue(self.use_case.commit(
            self.world, "handover", self.item.instance_id,
            ConsumptionOrigin.HANDOVER, self.inputs,
            memory_id=self.item.instance_id,
        ).accepted)
        self.assertGreater(self.pet.friendship, before.friendship)

    def test_failure_after_world_mutation_restores_both_owners(self):
        before = self.world.snapshot()
        original = self.world.consume

        def broken(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("injected partial failure")

        with patch.object(self.world, "consume", side_effect=broken):
            with self.assertRaises(RuntimeError):
                self.consume()
        self.assertEqual(self.world.snapshot(), before)
        self.assertEqual(self.pet.satiety, 50)
        self.assertTrue(self.consume().accepted)
