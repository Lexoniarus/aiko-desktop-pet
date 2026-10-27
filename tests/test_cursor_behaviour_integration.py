"""Real headless observation, policy, driver and animation cooperate."""

import unittest
from dataclasses import replace

from aiko_pet.application.cursor_behaviour import (
    CursorActivityContext,
    CursorBehaviourCoordinator,
)
from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts,
    DesktopAnimationRuntime,
)
from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.desktop.visual_observation import (
    DesktopVisualObservation,
    VisualAttentionPorts,
)
from aiko_pet.desktop.walk_runtime import WalkDriver, WalkDriverPorts
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.cursor_attention import CursorAttention
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot


class IdleComputer:
    def latest(self):
        return ComputerSnapshot(cpu=2)


class CursorIntegrationTests(unittest.TestCase):
    def test_calm_pointer_turns_then_takes_one_bounded_step_and_recovers(self):
        settings = PetSettings(
            x=100, scale=1, auto_walk=True, follow_cursor=True, observe_computer=False
        )
        state = PetState()
        observer = CursorObservation(CursorAttention())
        coordinator = CursorBehaviourCoordinator(
            state, settings, observer, CursorBehaviourPolicy()
        )
        clock = [0.0]
        activity = [CursorActivityContext()]

        def place(x):
            settings.x = round(x)

        walk = WalkDriver(
            state=state,
            settings=settings,
            adaptive=AdaptiveRoutine(),
            monitor=IdleComputer(),
            walk_cycle_seconds=1.28,
            ports=WalkDriverPorts(
                track=lambda: TaskbarTrack(0, 1200, 600),
                menu_engaged=lambda: False,
                place_x=place,
                walk_finished=lambda _: None,
                cursor_allowed=lambda: coordinator.admit_motion(activity[0], clock[0])
                is not None,
                cursor_finished=coordinator.finish_motion,
            ),
        )
        walk.movement.random_walk.next_walk_at = 999
        visual = DesktopVisualObservation(
            settings=settings,
            monitor=IdleComputer(),
            eyes=lambda: ((settings.x or 0) + 96, 82),
            attention=VisualAttentionPorts(
                cursor_intent=lambda: coordinator.intent
            ),
        )
        runtime = DesktopAnimationRuntime(
            state=state,
            settings=settings,
            assets=load_character_catalog(),
            walk=walk,
            visual=visual,
            ports=AnimationRuntimePorts(
                action_until=lambda: 0,
                action_clip_id=lambda: "idle",
                attention_until=lambda: 0,
            ),
        )
        before = settings.x
        seen = []
        for i in range(80):
            now = i * 0.14
            clock[0] = now
            observer.observe(
                (420, 194),
                now,
                game_mode=False,
                eyes=((settings.x or 0) + 96, 82),
                screen_width=1200,
            )
            coordinator.begin_frame(now, activity[0])
            walk.apply_cursor_intent(coordinator.admit_motion(activity[0], now), now)
            choice = runtime.select_animation(
                now, (420, 194), observer.attention.last_pointer_move, False, None
            )
            seen.append(choice.sprite.animation)
            if choice.sprite.animation.startswith("body-step"):
                runtime.advance_walk(now, 0.14, game_mode=False)
        self.assertEqual(settings.x, (before or 0) + 16)
        self.assertTrue(any(n.startswith("body-orient-right") for n in seen))
        self.assertTrue(any(n.startswith("body-step-right") for n in seen))
        self.assertFalse(coordinator.intent.moving)
        activity[0] = replace(activity[0], world_protected=True)
        self.assertIsNone(coordinator.admit_motion(activity[0], clock[0]))
