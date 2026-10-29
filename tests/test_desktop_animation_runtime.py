"""Desktop animation intent is selected without constructing Tk sprites."""

from __future__ import annotations

import unittest
from dataclasses import replace
from types import MappingProxyType
from typing import cast
from unittest.mock import MagicMock, patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts,
    DesktopAnimationRuntime,
)
from aiko_pet.desktop.visual_observation import DesktopVisualObservation
from aiko_pet.desktop.walk_runtime import WalkDriver
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.animation.ambient import AmbientDirector
from aiko_pet.pet.animation.animation import PassiveObservation, SpriteSelection
from aiko_pet.pet.animation.expression import Expression
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.mind.cursor_behaviour import CursorIntent
from aiko_pet.pet.movement.contracts import WalkStep
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class DesktopAnimationRuntimeTests(unittest.TestCase):
    def test_face_does_not_start_an_action_or_interrupt_walking_and_gaze(self):
        self.choose()
        with patch("aiko_pet.desktop.animation_runtime.time.monotonic",
                   return_value=100):
            self.assertTrue(self.runtime.request_expression(Expression.POSITIVE))
        self.assertEqual(self.choose().sprite,
                         SpriteSelection("expression-positive", 0))
        self.walk.movement.interrupt.assert_not_called()
        self.assertEqual(self.action_until, 0)
        self.visual.observe.return_value = PassiveObservation(12, False)
        self.assertEqual(self.choose(now=100.1).sprite, SpriteSelection("look", 12))
        self.visual.observe.return_value = PassiveObservation(None, False)
        self.assertEqual(self.choose(now=100.2).sprite,
                         SpriteSelection("rest-neutral", 0))

    def test_face_is_rejected_during_custody_sleep_and_existing_body_actions(self):
        for blocker in ("book", "handover", "sleep", "action", "walk"):
            with self.subTest(blocker=blocker):
                self.create_runtime_fixture()
                self.choose()
                self.holding_readable = blocker == "book"
                self.ready_for_handover = blocker == "handover"
                set_test_pet_values(self.state, sleeping=blocker == "sleep")
                self.action_until = 200 if blocker == "action" else 0
                self.walk.movement.remaining_distance = 20 if blocker == "walk" else 0
                with patch("aiko_pet.desktop.animation_runtime.time.monotonic",
                           return_value=100):
                    self.assertFalse(self.runtime.request_expression(Expression.FIRM))

    def test_game_rest_blinks_without_turning_or_resetting_the_sway(self):
        self.runtime.ambient = AmbientDirector(100)
        self.runtime.ambient.next_blink_at = 101
        self.runtime.ambient.next_glance_at = 100
        self.choose(now=100, game_mode=True)
        self.assertEqual(self.choose(now=101, game_mode=True).sprite,
                         SpriteSelection("rest-neutral", 2))
        self.assertEqual(self.choose(now=101.07, game_mode=True).sprite,
                         SpriteSelection("rest-neutral", 3))
        self.assertEqual(self.runtime.ambient.motion_offset(101), 1)

    def test_game_uses_new_rest_but_a_real_jump_still_wins(self):
        self.assertEqual(self.choose(game_mode=True).sprite,
                         SpriteSelection("rest-neutral", 0))
        with patch("aiko_pet.desktop.animation_runtime.time.monotonic",
                   return_value=100):
            self.assertTrue(self.runtime.request_expression(Expression.DOWNCAST))
        self.assertEqual(self.choose(game_mode=True).sprite,
                         SpriteSelection("expression-downcast", 0))
        self.assertEqual(self.choose(game_mode=True, active_action="jumping").sprite,
                         SpriteSelection("jumping"))
        self.assertEqual(self.choose(game_mode=True).sprite,
                         SpriteSelection("rest-neutral", 0))

    def test_main_tick_profile_is_shared_and_frames_do_not_replace_it(self):
        from aiko_pet.pet.animation.idle_behaviour import IdleBehaviourProfile

        profile = IdleBehaviourProfile(mode="tired", maximum_steps=1)
        self.runtime.set_idle_profile(profile)
        for now in (100, 100.1, 101):
            self.choose(now=now)
            self.assertIs(self.runtime.ambient.profile, profile)
            self.assertIs(self.walk.idle_profile, profile)

    def setUp(self) -> None:
        self.create_runtime_fixture()

    def create_runtime_fixture(self) -> None:
        self.state = PetState()
        self.settings = PetSettings()
        self.walk = MagicMock(spec=WalkDriver)
        self.walk.movement = MagicMock()
        self.walk.movement.remaining_distance = 0
        self.walk.step.return_value = None
        self.visual = MagicMock(spec=DesktopVisualObservation)
        self.visual.observe.return_value = PassiveObservation(None, False)
        self.visual.orienting = False
        self.visual.cursor_watching = False
        self.visual.cursor_intent = CursorIntent()
        self.action_until = 0.0
        self.action_clip_id = "review"
        self.holding_readable = False
        self.ready_for_handover = False
        self.assets = load_character_catalog()
        self.runtime = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=self.assets,
            walk=cast(WalkDriver, self.walk),
            visual=cast(DesktopVisualObservation, self.visual),
            ports=AnimationRuntimePorts(
                action_until=lambda: self.action_until,
                action_clip_id=lambda: self.action_clip_id,
                holding_readable=lambda: self.holding_readable,
                ready_for_handover=lambda: self.ready_for_handover,
            ),
        )
        self.runtime.ambient.next_blink_at = 1000.0
        self.runtime.ambient.next_glance_at = 1000.0

    def choose(
        self,
        *,
        now: float = 100.0,
        game_mode: bool = False,
        active_action: str | None = None,
    ) -> RenderDecision:
        return self.runtime.select_animation(
            now,
            (100, 0),
            now - 1,
            game_mode,
            active_action,
        )

    def test_game_one_shot_preempts_sleep_and_hardware(self) -> None:
        set_test_pet_values(self.state, sleeping=True)
        self.assertEqual(
            self.choose(game_mode=True, active_action="jumping"),
            RenderDecision(SpriteSelection("jumping")),
        )
        self.walk.step.assert_not_called()
        self.visual.observe.assert_not_called()

    def test_sleep_interrupts_motion_and_clears_active_action(self) -> None:
        set_test_pet_values(self.state, sleeping=True)
        self.assertEqual(
            self.choose(active_action="eat"),
            RenderDecision(SpriteSelection("sleep"), clear_action=True),
        )
        self.walk.movement.interrupt.assert_called_once_with()
        self.visual.observe.assert_not_called()

    def test_active_timed_action_preempts_passive_observation(self) -> None:
        self.action_until = 200.0
        self.assertEqual(
            self.choose(),
            RenderDecision(SpriteSelection("review")),
        )
        self.visual.observe.assert_not_called()

    def test_walk_runs_before_observing_passive_gaze(self) -> None:
        self.walk.step.return_value = WalkStep(0, 1)
        self.assertEqual(
            self.choose(),
            RenderDecision(SpriteSelection("running-right"), clear_action=True),
        )
        self.visual.observe.assert_not_called()

    def test_passive_gaze_is_selected_only_after_walk_stops(self) -> None:
        self.visual.observe.return_value = PassiveObservation(4, False)
        self.assertEqual(
            self.choose(),
            RenderDecision(SpriteSelection("look", fixed_frame=4), clear_action=True),
        )
        self.visual.observe.assert_called_once_with(
            100.0,
            (100, 0),
            99.0,
            False,
            cursor_gaze_point=None,
        )

    def test_fast_walk_callback_still_uses_attention_window(self) -> None:
        self.runtime.advance_walk(100.0, 0.1, game_mode=False)
        self.walk.step.assert_called_once_with(
            100.0,
            0.1,
            game_mode=False,
            attention_active=False,
        )

    def test_deliberate_orientation_holds_walking_without_a_new_deadline(self):
        self.visual.orienting = True
        self.runtime.advance_walk(100, 0.1, game_mode=False)
        self.walk.step.assert_called_once_with(
            100,
            0.1,
            game_mode=False,
            attention_active=True,
        )

    def test_emotional_stand_keeps_body_intent_and_immediate_opposite_gaze(self):
        self.visual.cursor_watching = True
        self.visual.cursor_intent = CursorIntent(
            "observe", side=1, body="three_quarter", feeling="curiosity",
        )
        self.visual.desired_cursor_gaze.return_value = 4
        self.visual.observe.return_value = PassiveObservation(4, False)
        for now in (100, 100.1, 102):
            self.assertEqual(self.choose(now=now).sprite,
                             SpriteSelection("body-look-right", 4))
            self.assertEqual(self.runtime._body_orientation.phase, 4)
        self.visual.desired_cursor_gaze.return_value = 12
        self.visual.observe.return_value = PassiveObservation(12, False)
        self.assertEqual(self.choose(now=102.1).sprite, SpriteSelection("look", 12))
        self.assertEqual(self.runtime._body_orientation.phase, 0)
        # The policy has not approved a leftward body yet; the head still follows.
        self.assertEqual(self.choose(now=102.2).sprite, SpriteSelection("look", 12))
        self.visual.cursor_intent = replace(self.visual.cursor_intent, side=-1)
        self.assertEqual(self.choose(now=104).sprite,
                         SpriteSelection("body-look-left", 5))
        self.visual.desired_cursor_gaze.return_value = None
        self.assertEqual(self.choose(now=104.1).sprite,
                         SpriteSelection("rest-neutral", 0))
        self.assertEqual(self.runtime._body_orientation.phase, 0)

    def test_finished_cursor_profile_settles_to_compatible_quarter_without_front(self):
        self.visual.cursor_watching = True
        self.visual.cursor_intent = CursorIntent(
            "observe", side=1, body="three_quarter", feeling="curiosity",
        )
        self.visual.desired_cursor_gaze.return_value = 3
        self.visual.observe.return_value = PassiveObservation(3, False)
        body = self.runtime._body_orientation
        body.orient_for_gaze_motion(99, 3)
        body.orient_for_gaze_motion(99.07, 3)
        self.assertTrue(body.motion_ready)
        self.assertEqual(self.choose().sprite, SpriteSelection("body-look-right", 3))
        self.assertFalse(body.motion_ready)
        self.assertEqual(body.phase, 4)

    def test_idle_body_episode_uses_real_turns_settled_hold_and_ordered_return(self):
        policy = AmbientDirector(0, between=lambda low, _high: low,
                                 direction=lambda options: options[0], body_poses=True)
        policy.next_blink_at = 10000
        for now in (0, 5):
            policy.next_glance_at = now
            policy.choose(now)
            policy.choose(now + 3.1)
        policy.next_glance_at = 100
        self.runtime.ambient = policy
        result = self.choose(now=100)
        self.assertEqual(self.runtime._body_orientation.phase, 1)
        self.assertEqual(result.refresh_after_ms, 140)
        for n in range(1, 4):
            result = self.choose(now=100 + n * .14)
            self.assertEqual(self.runtime._body_orientation.phase, n + 1)
            self.assertEqual(result.refresh_after_ms, 140 if n < 3 else None)
        self.assertEqual(result.sprite, SpriteSelection("body-look-right", 2))
        self.assertAlmostEqual(policy._glance_until, 103.42)
        self.assertEqual(self.choose(now=102).sprite,
                         SpriteSelection("body-look-right", 3))
        result = self.choose(now=103.5)
        self.assertEqual(self.runtime._body_orientation.phase, 3)
        for n in range(1, 4):
            result = self.choose(now=103.5 + n * .14)
            self.assertEqual(self.runtime._body_orientation.phase, 3 - n)
        self.assertEqual(result.sprite, SpriteSelection("rest-neutral", 0))
        self.assertEqual(self.settings.x, None)

    def test_final_idle_displacement_admits_one_hold_after_movement_suspension(self):
        self.runtime.ambient = AmbientDirector(
            0, between=lambda low, _high: low, body_poses=True,
            direction=lambda options: options[0],
        )
        self.runtime.ambient.next_blink_at = 10000
        self.walk.movement.source = "idle"
        self.walk.movement.kind = "step"
        self.walk.movement.remaining_distance = 1
        for n in range(8):
            self.runtime._body_orientation.orient_for_motion(97 + n * .14, 1)

        def step(_now, elapsed, **_kwargs):
            if elapsed:
                self.walk.movement.remaining_distance = 0
                return WalkStep(1, 1, "step")
            return None

        self.walk.step.side_effect = step
        before = self.state.capture_checkpoint()
        self.runtime.advance_walk(100, .033, game_mode=False)
        self.assertEqual(self.runtime.ambient._outing_count, 1)
        result = self.choose(now=100)
        self.assertEqual(self.runtime._body_orientation.phase, 7)
        for n in range(1, 4):
            result = self.choose(now=100 + n * .14)
            self.assertEqual(self.runtime._body_orientation.phase, 7 - n)
        self.assertEqual(result.sprite, SpriteSelection("body-look-right", 4))
        self.assertEqual(self.runtime.ambient._outing_count, 1)
        self.assertEqual(self.choose(now=102).sprite,
                         SpriteSelection("body-look-right", 2))
        self.assertEqual(self.state.capture_checkpoint(), before)

    def test_cursor_and_world_completions_never_create_idle_arrival_poses(self):
        for source in ("cursor", "world"):
            self.create_runtime_fixture()
            self.walk.movement.source = source
            self.walk.movement.kind = "step"
            self.walk.movement.remaining_distance = 0
            for n in range(8):
                self.runtime._body_orientation.orient_for_motion(97 + n * .14, 1)
            self.walk.step.return_value = WalkStep(1, 1, "step")
            self.runtime.advance_walk(100, .033, game_mode=False)
            self.assertEqual(self.runtime.ambient._outing_count, 0)

    def test_optional_pack_missing_preserves_frontal_gaze_after_long_attention(self):
        runtime = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=replace(self.assets, body_clips=MappingProxyType({})),
            walk=cast(WalkDriver, self.walk),
            visual=cast(DesktopVisualObservation, self.visual),
            ports=AnimationRuntimePorts(
                action_until=lambda: 0.0,
                action_clip_id=lambda: "idle",
            ),
        )
        runtime.ambient.next_blink_at = runtime.ambient.next_glance_at = 1000.0
        self.visual.observe.return_value = PassiveObservation(4, False)
        for now in (100.0, 102.0, 104.0):
            self.assertEqual(
                runtime.select_animation(now, (100, 0), now - 1, False, None),
                RenderDecision(SpriteSelection("look", 4), clear_action=True),
            )

    def test_older_optional_pack_uses_existing_motion_without_missing_clips(self):
        old_clips = {
            name: clip
            for name, clip in self.assets.body_clips.items()
            if name.startswith(("body-look-", "body-turn-"))
        }
        runtime = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=replace(self.assets, body_clips=MappingProxyType(old_clips)),
            walk=cast(WalkDriver, self.walk),
            visual=cast(DesktopVisualObservation, self.visual),
            ports=AnimationRuntimePorts(
                action_until=lambda: 0.0,
                action_clip_id=lambda: "idle",
            ),
        )
        self.walk.movement.kind = "step"
        self.walk.movement.source = "cursor"
        self.walk.movement.remaining_distance = 16
        self.walk.step.return_value = WalkStep(0, 1, "step")
        self.assertEqual(
            runtime.select_animation(100, (100, 0), 99, False, None).sprite,
            SpriteSelection("running-right"),
        )
        self.assertEqual(
            runtime.advance_walk(100.1, 0.1, game_mode=False), "running-right"
        )
        self.assertEqual(self.walk.step.call_count, 2)

    def test_priority_resets_body_and_new_plan_restarts_steps(self) -> None:
        for priority in ("sleep", "game", "action", "walk", "handover", "book"):
            with self.subTest(priority=priority):
                self.create_runtime_fixture()
                self.visual.observe.return_value = PassiveObservation(4, False)
                self.visual.cursor_intent = CursorIntent("observe", side=1,
                                                       body="three_quarter")
                for now in (100, 101.20, 101.34, 101.48, 101.62):
                    turned = self.choose(now=now)
                self.assertEqual(turned.sprite, SpriteSelection("body-look-right", 4))
                set_test_pet_values(self.state, sleeping=priority == "sleep")
                self.action_until = 200 if priority == "action" else 0
                self.walk.step.return_value = (
                    WalkStep(0, 1) if priority == "walk" else None
                )
                self.ready_for_handover = priority == "handover"
                self.holding_readable = priority == "book"
                interrupted = self.choose(now=102, game_mode=priority == "game")
                self.assertFalse(interrupted.sprite.animation.startswith("body-"))
                set_test_pet_values(self.state, sleeping=False)
                self.action_until = 0
                self.walk.step.return_value = None
                self.ready_for_handover = self.holding_readable = False
                self.visual.cursor_intent = CursorIntent("observe")
                for now in (103, 104):
                    self.assertEqual(
                        self.choose(now=now).sprite, SpriteSelection("look", 4)
                    )
                self.visual.cursor_intent = CursorIntent("observe", side=1,
                                                       body="three_quarter")
                self.assertEqual(
                    self.choose(now=104.2).sprite, SpriteSelection("body-turn-right", 1)
                )
