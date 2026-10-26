"""READ failures safely release the shared held-object phase without nutrition."""

import unittest
from unittest.mock import Mock

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.mind.object_decisions import ObjectUseDecision
from aiko_pet.pet.mind.object_intentions import ObjectGoal
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldSurface,
)
from aiko_pet.world.state import WorldState


class ReadableInteractionTests(unittest.TestCase):
    def setUp(self):
        self.world = WorldState(
            WorldSurface(800, 600),
            (
                ObjectDefinition(
                    "book", "book", interactions=frozenset((ObjectInteraction.READ,))
                ),
            ),
        )
        self.item = self.world.place_resting("book", 100, ObjectFootprint(32, 32))
        self.memory = ObjectMemory()
        self.memory.update(
            (
                ObjectObservation(
                    self.item.instance_id, "book", "book", 100, 0, True, 0
                ),
            ),
            now=0,
        )
        self.actions = []

        def play(name):
            self.actions.append(name)
            return len(self.actions)

        self.consume = Mock()
        self.owner = ObjectInteractionCoordinator(
            self.world,
            play=play,
            stop=Mock(),
            select_item=Mock(),
            consume=self.consume,
            can_acquire=lambda token: True,
            ground_x=lambda token: 100,
            completed=Mock(),
            memory=self.memory,
            resolve_instance=lambda token: token,
            record_for_instance=lambda token: token,
            decide=lambda token, context: ObjectUseDecision(False, "read", read=True),
            feedback=lambda cue: self.owner.receive_feedback(
                FeedbackReceipt(cue.key, True)
            ),
            hand_type_conflicts=lambda record, instance: False,
            cancel_feedback=Mock(),
            now=lambda: 0,
            inspection_seconds=0,
        )
        self.owner.can_read = lambda token, personal: True

    def grasp(self):
        self.owner.begin_goal(
            ObjectGoal(self.item.instance_id, "book", "book", 100, 0, 0)
        )
        self.owner.arrive()
        self.owner.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        self.owner.receive(PlaybackEvent(1, "pick_up", 7, finished=True))

    def assert_put_down(self):
        self.assertEqual(self.owner.phase, "put_down")
        self.owner.receive(PlaybackEvent(3, "put_down", 2, ("detach_object",)))
        self.owner.receive(PlaybackEvent(3, "put_down", 7, finished=True))
        self.assertEqual(
            self.world.get(self.item.instance_id).state, ObjectState.RESTING
        )
        self.consume.assert_not_called()

    def test_reader_decline_puts_the_book_down(self):
        self.owner.read_book = Mock(return_value=False)
        self.grasp()
        self.assert_put_down()

    def test_unexpected_reader_exception_unwinds_the_physical_phase(self):
        self.owner.read_book = Mock(side_effect=ModuleNotFoundError("astronomy"))
        with self.assertRaises(ModuleNotFoundError):
            self.grasp()
        self.assert_put_down()

    def test_finished_reader_returns_to_the_same_put_down_episode(self):
        reader = Mock(return_value=True)
        self.owner.read_book = reader
        self.grasp()
        self.assertEqual(self.owner.phase, "read")
        reader.call_args.args[1](True)
        self.assert_put_down()
