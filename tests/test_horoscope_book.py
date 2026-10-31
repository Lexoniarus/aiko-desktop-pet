"""Physical READ uses the shared custody phases, without nutrition."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from test_horoscope import NOW, coordinator

from aiko_pet.application.object_feedback import FeedbackReceipt
from aiko_pet.application.object_interaction import ObjectInteractionCoordinator
from aiko_pet.desktop.horoscope_playback import HoroscopePlayback
from aiko_pet.infrastructure.world_codec import decode_world, encode_world
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.mind.object_decisions import ObjectUseDecision
from aiko_pet.pet.mind.object_intentions import ObjectGoal
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.reaction_test_support import FakeScheduler


def book_world():
    world = WorldState(
        WorldSurface(800, 600),
        (
            ObjectDefinition(
                "horoscope_book",
                "horoscope_book",
                interactions=frozenset((ObjectInteraction.READ,)),
            ),
        ),
    )
    item = world.place_resting("horoscope_book", 100, ObjectFootprint(10, 10))
    return world, item


class HoroscopeBookTests(unittest.TestCase):
    def test_shared_pickup_read_putdown_never_consumes_book(self):
        world, item = book_world()
        memory = ObjectMemory()
        memory.update(
            (
                ObjectObservation(
                    item.instance_id, "horoscope_book", "book", 100, 0, True, 0
                ),
            ),
            now=0,
        )
        actions = []
        consumed, put_down, finish_reading = Mock(), Mock(), Mock(return_value=True)

        def play(name):
            actions.append(name)
            return len(actions)

        owner = ObjectInteractionCoordinator(
            world,
            play=play,
            stop=Mock(),
            select_item=Mock(),
            consume=consumed,
            can_acquire=lambda token: True,
            ground_x=lambda token: 100,
            completed=Mock(),
            memory=memory,
            resolve_instance=lambda token: token,
            record_for_instance=lambda token: token,
            decide=lambda token, context: ObjectUseDecision(False, "read", read=True),
            feedback=lambda cue: owner.receive_feedback(FeedbackReceipt(cue.key, True)),
            inspection_seconds=0,
            hand_type_conflicts=lambda record, instance: False,
            cancel_feedback=Mock(),
            now=lambda: 0,
        )
        owner.can_read = lambda token, personal: True
        owner.read_book = finish_reading
        owner.book_put_down = put_down
        owner.begin_goal(
            ObjectGoal(item.instance_id, "horoscope_book", "book", 100, 0, 0)
        )
        owner.arrive()
        owner.receive(PlaybackEvent(1, "pick_up", 3, ("attach_object",)))
        owner.receive(PlaybackEvent(1, "pick_up", 7, finished=True))
        self.assertEqual(owner.phase, "read")
        self.assertEqual(world.get(item.instance_id).state, ObjectState.PET_HELD)
        self.assertEqual(actions, ["pick_up", "hold_item"])
        finish_reading.call_args.args[1](True)
        self.assertEqual(owner.phase, "put_down")
        owner.receive(PlaybackEvent(3, "put_down", 3, ("detach_object",)))
        owner.receive(PlaybackEvent(3, "put_down", 7, finished=True))
        self.assertEqual(world.get(item.instance_id).state, ObjectState.RESTING)
        put_down.assert_called_once_with(item.instance_id)
        consumed.assert_not_called()

    def test_deadline_survives_world_codec_and_expires_any_custody(self):
        for custody in ("resting", "user", "pet"):
            with self.subTest(custody=custody):
                world, item = book_world()
                if custody == "user":
                    world.take_resting(
                        item.instance_id, expected_revision=item.revision
                    )
                elif custody == "pet":
                    world.collect_resting(
                        item.instance_id, expected_revision=item.revision
                    )
                world.set_book_expiry(item.instance_id, NOW + 3600)
                saved = encode_world(world.snapshot(), recovery_x=100)
                restored = decode_world(saved, world.snapshot().definitions)
                self.assertEqual(restored.objects[0].expires_at, NOW + 3600)
                with self.assertRaises(ValueError):
                    world.set_book_expiry(item.instance_id, NOW + 7200)
                self.assertFalse(world.expire_books(NOW + 3599.99))
                self.assertEqual(world.expire_books(NOW + 3600), (item.instance_id,))
                self.assertEqual(world.get(item.instance_id).state, ObjectState.REMOVED)

    def test_opening_cancellation_invalidates_queued_read_callback(self):
        content, _clock, _sky, _credit = coordinator()
        scheduler = FakeScheduler()
        player = ReactionPlayer(
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            display_text=Mock(),
            display_emote=Mock(),
            start_action=Mock(),
            mark_spoken=Mock(),
            is_closed=lambda: False,
        )
        pose, completed = Mock(), Mock()
        reading = HoroscopePlayback(
            content,
            player,
            pose,
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
        )
        self.assertTrue(reading.start("object_1", completed))
        self.assertFalse(player.active)
        reading.stop()
        completed.assert_called_once_with(False)
        self.assertFalse(reading.active)
        self.assertFalse(player.active)

    def test_late_calculation_failure_declines_without_leaving_playback_active(self):
        content, _clock, sky, credit = coordinator()
        sky.calculate.side_effect = ModuleNotFoundError("astronomy")
        scheduler = FakeScheduler()
        player = ReactionPlayer(
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            display_text=Mock(),
            display_emote=Mock(),
            start_action=Mock(),
            mark_spoken=Mock(),
            is_closed=lambda: False,
        )
        unavailable = Mock()
        reading = HoroscopePlayback(
            content,
            player,
            Mock(),
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            unavailable=unavailable,
        )
        with self.assertLogs("aiko_pet.desktop.horoscope_playback", level="WARNING"):
            self.assertFalse(reading.start("object_1", Mock()))
        self.assertFalse(reading.active)
        self.assertFalse(player.active)
        self.assertFalse(content.history.days)
        credit.assert_not_called()
        unavailable.assert_called_once_with()
