"""Desktop animation intent is selected without constructing Tk sprites."""

from __future__ import annotations

import unittest
from typing import cast
from unittest.mock import MagicMock

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts, DesktopAnimationRuntime,
)
from aiko_pet.desktop.visual_observation import DesktopVisualObservation
from aiko_pet.desktop.walk_runtime import WalkDriver
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.animation.animation import PassiveObservation, SpriteSelection
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.state import PetState


class DesktopAnimationRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = PetState()
        self.settings = PetSettings()
        self.walk = MagicMock(spec=WalkDriver)
        self.walk.movement = MagicMock()
        self.walk.movement.remaining_distance = 0
        self.walk.step.return_value = None
        self.visual = MagicMock(spec=DesktopVisualObservation)
        self.visual.observe.return_value = PassiveObservation(None, False)
        self.action_until = 0.0
        self.action_clip_id = "review"
        self.runtime = DesktopAnimationRuntime(
            state=self.state, settings=self.settings,
            assets=load_character_catalog(),
            walk=cast(WalkDriver, self.walk),
            visual=cast(DesktopVisualObservation, self.visual),
            ports=AnimationRuntimePorts(
                action_until=lambda: self.action_until,
                action_clip_id=lambda: self.action_clip_id,
                attention_until=lambda: -100.0,
            ),
        )
        self.runtime.ambient.next_blink_at = 1000.0
        self.runtime.ambient.next_glance_at = 1000.0

    def choose(
        self, *, now: float = 100.0, game_mode: bool = False,
        active_action: str | None = None,
    ) -> RenderDecision:
        return self.runtime.select_animation(
            now, (100, 0), now - 1, game_mode, active_action,
        )

    def test_game_one_shot_preempts_sleep_and_hardware(self) -> None:
        self.state.sleeping = True
        self.assertEqual(
            self.choose(game_mode=True, active_action="jumping"),
            RenderDecision(SpriteSelection("jumping")),
        )
        self.walk.step.assert_not_called()
        self.visual.observe.assert_not_called()

    def test_sleep_interrupts_motion_and_clears_active_action(self) -> None:
        self.state.sleeping = True
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
        self.walk.step.return_value = "running-right"
        self.assertEqual(
            self.choose(),
            RenderDecision(SpriteSelection("running-right"), clear_action=True),
        )
        self.visual.observe.assert_not_called()

    def test_passive_gaze_is_selected_only_after_walk_stops(self) -> None:
        self.visual.observe.return_value = PassiveObservation(4, False)
        self.assertEqual(
            self.choose(),
            RenderDecision(SpriteSelection("look", fixed_frame=4),
                           clear_action=True),
        )
        self.visual.observe.assert_called_once_with(
            100.0, (100, 0), 99.0, False,
        )

    def test_fast_walk_callback_still_uses_attention_window(self) -> None:
        self.runtime.advance_walk(100.0, 0.1, game_mode=False)
        self.walk.step.assert_called_once_with(
            100.0, 0.1, game_mode=False, attention_active=False,
        )
