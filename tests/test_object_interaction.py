"""Grasp is distinct from nutrition; interruption safely reverses ownership."""

import unittest

from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ObjectInteractionTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        self.item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.actions = []
        self.consumed = []
        self.done = []

        def play(clip):
            self.actions.append(clip)
            return len(self.actions)

        def consume(key, item_id, origin):
            self.consumed.append((key, item_id, origin))
            item = self.world.get(item_id)
            self.world.consume(item_id, expected_revision=item.revision)
            return True

        self.coordinator = ObjectInteractionCoordinator(
            self.world, play=play, stop=lambda: None, select_item=lambda _item: None,
            consume=consume, eligible=lambda _item: True, ground_x=lambda _item: 100,
            completed=lambda item, consumed: self.done.append((item, consumed)),
        )

    def test_acquisition_precedes_consumption_and_duplicates_are_ignored(self):
        self.coordinator.begin_pickup(self.item.instance_id)
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

    def test_interruption_after_grasp_puts_down_before_user_action(self):
        self.coordinator.begin_pickup(self.item.instance_id)
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
        self.coordinator.begin_pickup(self.item.instance_id)
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
        self.coordinator.begin_pickup(self.item.instance_id)
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.coordinator.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.coordinator.interrupt(lambda: self.actions.append("talk"))
        self.assertEqual(self.done, [(self.item.instance_id, True)])
        self.assertEqual(self.actions[-1], "talk")
        self.assertEqual(len(self.consumed), 1)
