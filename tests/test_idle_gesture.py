"""Grounded requests wait for front, preserve artwork and never acknowledge care."""

import unittest
from dataclasses import replace
from unittest.mock import Mock

import test_attention_policy as policy_support
import test_desktop_animation_runtime as animation_support
import test_desktop_attention_runtime as runtime_support

from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.animation.animation import FrameClock
from aiko_pet.pet.animation.idle_gesture import (
    QUESTION_REQUEST_CLIP,
    IdleGestureChoice,
    with_idle_gestures,
)
from aiko_pet.pet.wishes import ActiveWish, WishId, WishState
from tools.pet_test_support import set_test_pet_values


class IdleGestureTests(unittest.TestCase):
    def setUp(self):
        fixture = policy_support.AttentionPolicyTests()
        fixture.setUp()
        self.attention = fixture.attention
        self.state = fixture.state
        set_test_pet_values(self.state, friendship=50, mood=75)
        self.state.restore_checkpoint(replace(
            self.state.capture_checkpoint(), lived_seconds=100,
            wishes=WishState(2, (ActiveWish(1, WishId.FOOD, "apple", 0, 200),)),
        ))
        self.attention.next_idle_emote = 0

    def test_real_request_is_read_only_and_uses_existing_cooldown(self):
        before = self.state.capture_checkpoint()
        choice = self.attention.select_idle_animation(
            100, action_until=0, walking=False,
        )
        self.assertEqual(choice, IdleGestureChoice(1))
        self.assertIsNone(self.attention.select_idle_animation(
            100.1, action_until=0, walking=False,
        ))
        self.assertEqual(self.state.capture_checkpoint(), before)
        self.assertIsNone(self.state.wishes.active[0].expressed_at)

    def test_missing_expired_spoken_or_restricted_wish_stays_silent(self):
        original = self.state.capture_checkpoint()
        for wish in (None, ActiveWish(1, WishId.FOOD, "apple", 0, 99),
                     ActiveWish(1, WishId.FOOD, "apple", 0, 200, expressed_at=90),
                     ActiveWish(1, WishId.FACT, "fact", 0, 200),
                     ActiveWish(1, WishId.WIN_ROUND, "blackjack", 0, 200)):
            with self.subTest(wish=wish):
                self.state.restore_checkpoint(replace(
                    original, wishes=WishState(2, (wish,) if wish else ()),
                ))
                self.assertIsNone(self.attention.idle_gesture_choice())
        self.state.restore_checkpoint(original)
        set_test_pet_values(self.state, friendship=0)
        self.assertIsNone(self.attention.idle_gesture_choice())

    def test_one_shot_alias_reuses_every_source_frame_and_anchor(self):
        original = load_character_catalog()
        catalog = with_idle_gestures(original)
        request = catalog.clips[QUESTION_REQUEST_CLIP]
        source = original.clips["waiting"]
        self.assertIs(request.frames, source.frames)
        self.assertEqual(request.timings, source.timings)
        self.assertEqual(request.anchor, source.anchor)
        self.assertFalse(request.loop)
        self.assertEqual(request.return_to, "idle")
        self.assertTrue(original.clips["waiting"].loop)
        self.assertEqual({k: catalog.clips[k] for k in original.clips}, original.clips)
        clock = FrameClock(started_at=100)
        now = 100.0
        for index, duration in enumerate(request.timings):
            self.assertEqual(clock.next_index(
                request.name, now, request.timings, loop=False), index)
            self.assertFalse(clock.finished)
            now += duration / 1000 + .001
        clock.next_index(request.name, now, request.timings, loop=False)
        self.assertTrue(clock.finished)

    def test_quarter_returns_through_real_phases_before_gesture_is_ready(self):
        fixture = animation_support.DesktopAnimationRuntimeTests()
        fixture.setUp()
        fixture.visual.object_target = None
        body = fixture.runtime._body_orientation
        body.side, body.phase = 1, 4
        self.assertEqual(fixture.runtime.prepare_idle_gesture(True, 100), "turning")
        phases = []
        for now in (100, 100.15, 100.30, 100.45):
            fixture.choose(now=now)
            phases.append(body.phase)
        self.assertEqual(phases, [3, 2, 1, 0])
        self.assertEqual(fixture.runtime.prepare_idle_gesture(True, 101), "ready")
        fixture.visual.cursor_watching = True
        self.assertEqual(fixture.runtime.prepare_idle_gesture(True, 101), "blocked")
        self.assertFalse(fixture.runtime._idle_gesture_front)

    def test_cursor_preempts_running_idle_gesture_through_existing_action_owner(self):
        fixture = animation_support.DesktopAnimationRuntimeTests()
        fixture.setUp()
        fixture.runtime._assets = with_idle_gestures(fixture.assets)
        fixture.visual.object_target = None
        fixture.visual.cursor_watching = True
        cancel = Mock(side_effect=lambda now: setattr(fixture, "action_until", now))
        fixture.runtime._ports = replace(fixture.runtime._ports, cancel_action=cancel)
        fixture.action_until = 104.57
        fixture.action_clip_id = QUESTION_REQUEST_CLIP
        decision = fixture.choose(now=101, active_action=QUESTION_REQUEST_CLIP)
        cancel.assert_called_once_with(101)
        self.assertEqual(fixture.action_until, 101)
        self.assertNotEqual(decision.sprite.animation, QUESTION_REQUEST_CLIP)

    def runtime_fixture(self):
        fixture = runtime_support.DesktopAttentionRuntimeTests()
        fixture.setUp()
        fixture.attention.select_idle_animation.return_value = IdleGestureChoice(1)
        fixture.attention.idle_gesture_choice.return_value = IdleGestureChoice(1)
        fixture.attention.next_idle_emote = 200
        fixture.runtime._ports = replace(
            fixture.runtime._ports,
            prepare_idle_gesture=Mock(return_value="turning"),
            idle_gesture_duration=lambda _: 4.57,
        )
        return fixture

    def test_ready_request_plays_one_full_cycle_without_wish_text_ack(self):
        fixture = self.runtime_fixture()
        fixture.runtime.maybe_show_idle_emote(100)
        fixture.presenter.show_animation.assert_not_called()
        fixture.runtime._ports = replace(
            fixture.runtime._ports, prepare_idle_gesture=Mock(return_value="ready"),
        )
        fixture.runtime.maybe_show_idle_emote(101)
        fixture.presenter.show_animation.assert_called_once_with(
            QUESTION_REQUEST_CLIP, 4.57,
        )
        fixture.attention.note_wish_text.assert_not_called()
        self.assertIsNone(fixture.runtime._idle_gesture)

    def test_wish_lost_or_real_action_during_turn_drops_without_replay(self):
        for guard in ("action", "expired", "cooldown"):
            fixture = self.runtime_fixture()
            fixture.runtime.maybe_show_idle_emote(100)
            if guard == "action":
                fixture.runtime._ports = replace(
                    fixture.runtime._ports, foreground_active=lambda: True,
                )
            elif guard == "expired":
                fixture.attention.idle_gesture_choice.return_value = None
            else:
                fixture.attention.next_idle_emote = 100.5
            fixture.runtime.maybe_show_idle_emote(101)
            self.assertIsNone(fixture.runtime._idle_gesture)
            fixture.presenter.show_animation.assert_not_called()


if __name__ == "__main__":
    unittest.main()
