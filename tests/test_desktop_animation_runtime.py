"""Desktop animation intent is selected without constructing Tk sprites."""

from __future__ import annotations

import unittest
from dataclasses import replace
from types import MappingProxyType
from typing import cast
from unittest.mock import MagicMock

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts,
    DesktopAnimationRuntime,
)
from aiko_pet.desktop.visual_observation import DesktopVisualObservation
from aiko_pet.desktop.walk_runtime import WalkDriver
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.animation.animation import PassiveObservation, SpriteSelection
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.movement.contracts import WalkStep
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class DesktopAnimationRuntimeTests(unittest.TestCase):
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
                attention_until=lambda: -100.0,
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
                attention_until=lambda: -100.0,
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
                attention_until=lambda: -100.0,
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

    def test_priority_interruptions_require_fresh_body_turn_dwell(self) -> None:
        for priority in ("sleep", "game", "action", "walk", "handover", "book"):
            with self.subTest(priority=priority):
                self.create_runtime_fixture()
                self.visual.observe.return_value = PassiveObservation(4, False)
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
                for now in (103, 104):
                    self.assertEqual(
                        self.choose(now=now).sprite, SpriteSelection("look", 4)
                    )
                self.assertEqual(
                    self.choose(now=104.2).sprite, SpriteSelection("body-turn-right", 1)
                )
