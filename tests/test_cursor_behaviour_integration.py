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
from aiko_pet.pet.interaction_events import CursorWarning, CursorWarningReceipt
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
            attention=VisualAttentionPorts(cursor_intent=lambda: coordinator.intent),
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


class CursorTrajectory:
    """Controlled lifecycle -> observation -> decision -> World admission -> render."""

    def __init__(self, scale=1, friendship=20, energy=80):
        self.now = 0.0
        self.scale = scale
        self.activity = CursorActivityContext()
        self.settings = PetSettings(
            x=500,
            scale=scale,
            auto_walk=True,
            follow_cursor=True,
            observe_computer=False,
        )
        self.state = PetState(
            updated_at=1800000000, energy=energy, friendship=friendship
        )
        self.observer = CursorObservation(CursorAttention())
        self.coordinator = CursorBehaviourCoordinator(
            self.state,
            self.settings,
            self.observer,
            CursorBehaviourPolicy(session_id="trajectory"),
        )
        self.completions = []
        self.feedback = []

        def place(x):
            self.settings.x = round(x)

        def completed(result):
            self.completions.append(result)
            self.coordinator.finish_motion(result)

        self.walk = WalkDriver(
            state=self.state,
            settings=self.settings,
            adaptive=AdaptiveRoutine(),
            monitor=IdleComputer(),
            walk_cycle_seconds=1.28,
            ports=WalkDriverPorts(
                track=lambda: TaskbarTrack(0, 4000, 800),
                menu_engaged=lambda: self.activity.menu_engaged,
                place_x=place,
                cursor_allowed=lambda: self.coordinator.admit_motion(
                    self.activity, self.now
                )
                is not None,
                cursor_finished=completed,
                idle_steps=lambda: True,
                hard_access=lambda: self.activity.direct_contact,
            ),
        )
        self.walk.movement.random_walk.next_walk_at = 999
        self.visual = DesktopVisualObservation(
            settings=self.settings,
            monitor=IdleComputer(),
            eyes=self.eyes,
            attention=VisualAttentionPorts(
                cursor_intent=lambda: self.coordinator.intent,
                walking=lambda: self.walk.movement.remaining_distance,
                walk_kind=lambda: self.walk.movement.kind,
            ),
        )
        self.runtime = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=load_character_catalog(),
            walk=self.walk,
            visual=self.visual,
            ports=AnimationRuntimePorts(
                action_until=lambda: 0, action_clip_id=lambda: "idle"
            ),
        )

    def eyes(self):
        return ((self.settings.x or 0) + 96 * self.scale, 82 * self.scale)

    def tick(self, point, dt=0.14):
        self.now += dt
        self.state.advance(1800000000 + self.now, elapsed_seconds=dt)
        self.observer.observe(
            point,
            self.now,
            game_mode=False,
            eyes=self.eyes(),
            screen_width=4000,
            scale=self.scale,
        )
        self.coordinator.begin_frame(self.now, self.activity)
        if isinstance(self.coordinator.feedback, CursorWarning):
            self.coordinator.note_warning(CursorWarningReceipt(
                self.coordinator.feedback.warning_id, self.now, True,
            ))
        elif self.coordinator.feedback is not None:
            self.feedback.append(self.coordinator.feedback)
        self.walk.apply_cursor_intent(
            self.coordinator.admit_motion(self.activity, self.now), self.now
        )
        choice = self.runtime.select_animation(
            self.now, point, self.observer.attention.last_pointer_move, False, None
        )
        self.runtime.advance_walk(self.now, dt, game_mode=False)
        return choice


class CompleteCursorTrajectoryTests(unittest.TestCase):
    def test_two_scales_trust_levels_turn_once_take_one_or_two_steps_then_front(self):
        for scale, friendship, steps in ((1, 10, 1), (2, 90, 2)):
            with self.subTest(scale=scale, friendship=friendship):
                scene = CursorTrajectory(scale, friendship)
                point = (500 + 320 * scale, 194 * scale)
                for _ in range(90):
                    scene.tick(point)
                self.assertEqual(scene.settings.x, 500 + steps * 16 * scale)
                self.assertEqual(len(scene.completions), 1)
                self.assertEqual(scene.completions[0].reason, "reached")
                self.assertEqual([e.feeling for e in scene.feedback], ["curiosity"])
                # Disengagement restores front without deleting the remaining moodlet.
                for _ in range(20):
                    scene.tick((3500, 100))
                self.assertEqual(scene.runtime._body_orientation.phase, 0)
                self.assertEqual(len(scene.state.moodlets.active), 1)

    def test_curiosity_then_real_threat_one_retreat_and_five_seconds_standing(self):
        for scale in (1, 2):
            scene = CursorTrajectory(scale, friendship=10)
            for _ in range(12):
                scene.tick((500 + 320 * scale, 194 * scale))
            # Establish far native motion then fast closing into the near region.
            scene.tick((500 + 550 * scale, 100 * scale))
            scene.tick((500 + 150 * scale, 100 * scale))
            self.assertFalse(scene.coordinator.intent.moving)
            scene.tick((500 + 550 * scale, 100 * scale))
            scene.tick((500 + 150 * scale, 100 * scale))
            self.assertEqual(scene.coordinator.intent.reaction, "flee")
            for _ in range(100):
                scene.tick((500 + 150 * scale, 100 * scale))
            self.assertEqual(len(scene.completions), 1)
            self.assertEqual(scene.completions[0].reason, "budget")
            self.assertEqual([e.feeling for e in scene.feedback], ["curiosity", "fear"])
            stopped_at = scene.settings.x
            for i in range(40):
                scene.tick((500 + (120 if i % 2 else 170) * scale, 100 * scale))
            self.assertEqual(scene.settings.x, stopped_at)
            self.assertEqual(len(scene.completions), 1)

    def test_foreground_suspends_evidence_and_contact_immediately_pauses(self):
        scene = CursorTrajectory()
        scene.activity = CursorActivityContext(foreground_active=True)
        for _ in range(40):
            scene.tick((820, 194))
        self.assertFalse(scene.feedback)
        self.assertEqual(scene.settings.x, 500)
        scene.activity = CursorActivityContext()
        for _ in range(40):
            scene.tick((820, 194))
        scene.coordinator.claim_access(scene.now)
        scene.walk.clear_cursor_request(scene.now)
        scene.activity = CursorActivityContext(direct_contact=True)
        stopped_at = scene.settings.x
        scene.walk.set_world_goal(900)
        for _ in range(40):
            scene.tick((820, 194))
        self.assertEqual(scene.settings.x, stopped_at)
        self.assertEqual(scene.walk.movement.goal_x, 900)
        self.assertEqual(len(scene.feedback), 1)

    def test_exhausted_pet_only_startles_and_keeps_frontal_body(self):
        scene = CursorTrajectory(energy=5)
        scene.tick((1050, 100))
        scene.tick((650, 100))
        self.assertFalse(scene.coordinator.intent.moving)
        scene.tick((1050, 100))
        scene.tick((650, 100))
        self.assertEqual(scene.coordinator.intent.reaction, "startle")
        self.assertEqual(scene.coordinator.intent.body, "front")
        for _ in range(50):
            scene.tick((650, 100))
        self.assertEqual(scene.settings.x, 500)
        self.assertFalse(scene.completions)
        self.assertEqual([e.feeling for e in scene.feedback], ["fear"])
