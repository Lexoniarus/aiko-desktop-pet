"""Real headless observation, policy, driver and animation cooperate."""

import math
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
from aiko_pet.pet.animation.body_orientation import body_look_index
from aiko_pet.pet.animation.gaze import gaze_sector
from aiko_pet.pet.cursor_experiences import cursor_impression
from aiko_pet.pet.interaction_events import CursorWarning, CursorWarningReceipt
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.cursor_attention import CursorAttention
from aiko_pet.pet.mind.cursor_behaviour import CursorBehaviourPolicy
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from tools.pet_test_support import set_test_pet_values


class IdleComputer:
    def latest(self):
        return ComputerSnapshot(cpu=2)


class CursorIntegrationTests(unittest.TestCase):
    def test_moving_pointer_turns_then_takes_one_bounded_step_and_recovers(self):
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
        for i in range(120):
            now = i * 0.14
            clock[0] = now
            point = (
                (round(196 + 192 * (2.4 + .7 * math.cos(i * .14 * 4.5))),
                 round(82 - 192 * (.8 + .7 * math.sin(i * .14 * 4.5))))
                if i < 65 else (420 if i == 65 else 540, 194)
            )
            observer.observe(
                point,
                now,
                game_mode=False,
                eyes=((settings.x or 0) + 96, 82),
                screen_width=1200,
            )
            coordinator.begin_frame(now, activity[0])
            walk.apply_cursor_intent(coordinator.admit_motion(activity[0], now), now)
            choice = runtime.select_animation(
                now, point, observer.attention.last_pointer_move, False, None
            )
            seen.append(choice.sprite.animation)
            if choice.sprite.animation.startswith("body-step"):
                runtime.advance_walk(now, 0.14, game_mode=False)
        final_x = settings.x
        assert final_x is not None
        self.assertGreater(final_x, (before or 0) + 16)
        self.assertLessEqual(final_x, 540 - 96)
        self.assertTrue(any(n == "body-look-right" for n in seen))
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

    def interest(self):
        for n in range(65):
            x, y = self.eyes()
            width = 192 * self.scale
            angle = n * .14 * 4.5
            self.tick((
                round(x + width * (2.4 + .7 * math.cos(angle))),
                round(y - width * (.8 + .7 * math.sin(angle))),
            ))

    def offer_moving_target(self):
        origin = self.settings.x or 0
        self.tick((origin + 320 * self.scale, 194 * self.scale))
        self.tick((origin + 440 * self.scale, 194 * self.scale))
        for _ in range(30):
            self.tick((origin + 440 * self.scale, 194 * self.scale))

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
    def test_two_scales_follow_high_pointer_then_release_when_it_stops(self):
        for scale, friendship in ((1, 10), (2, 90)):
            with self.subTest(scale=scale, friendship=friendship):
                scene = CursorTrajectory(scale, friendship)
                positions = []
                for n in range(90):
                    x, y = scene.eyes()
                    width = 192 * scale
                    choice = scene.tick((
                        round(x + width * (2.4 + .7 * math.cos(n * .63))),
                        round(y - width * (.8 + .7 * math.sin(n * .63))),
                    ))
                    positions.append(scene.settings.x)
                    if choice.sprite.animation.startswith("body-step"):
                        self.assertFalse(scene.observer.current.reachable)
                self.assertGreater(max(positions) - min(positions), 16 * scale)
                self.assertTrue(scene.completions)
                self.assertEqual([(e.feeling, e.level) for e in scene.feedback],
                                 [("curiosity", 1), ("curiosity", 2), ("curiosity", 3)]
                                 if friendship == 90 else
                                 [("curiosity", 1), ("curiosity", 2)])
                stopped_pointer = scene.observer.current.pointer
                for _ in range(30):
                    scene.tick(stopped_pointer)
                stopped_at = scene.settings.x
                for _ in range(30):
                    scene.tick(stopped_pointer)
                self.assertEqual(scene.settings.x, stopped_at)
                self.assertFalse(scene.coordinator.intent.moving)
                self.assertEqual(scene.runtime._body_orientation.phase, 0)
                self.assertEqual(len(scene.state.moodlets.active), 1)

    def test_curiosity_then_real_threat_one_retreat_and_five_seconds_standing(self):
        for scale in (1, 2):
            scene = CursorTrajectory(scale, friendship=10)
            scene.interest()
            set_test_pet_values(scene.state, mood=20)
            # Establish far native motion then fast closing into the near region.
            scene.tick((round(scene.eyes()[0] + 450 * scale), 100 * scale))
            scene.tick((round(scene.eyes()[0] + 54 * scale), 100 * scale))
            self.assertFalse(scene.coordinator.intent.moving)
            scene.tick((round(scene.eyes()[0] + 450 * scale), 100 * scale))
            scene.tick((round(scene.eyes()[0] + 54 * scale), 100 * scale))
            self.assertEqual(scene.coordinator.intent.reaction, "flee")
            fear_token = scene.coordinator.intent.token
            still = scene.observer.current.pointer
            for _ in range(100):
                scene.tick(still)
            retreats = [r for r in scene.completions if r.token == fear_token]
            self.assertEqual(len(retreats), 1)
            self.assertEqual(retreats[0].reason, "budget")
            self.assertEqual([e.feeling for e in scene.feedback], ["curiosity", "fear"])
            stopped_at = scene.settings.x
            count = len(scene.completions)
            for _ in range(25):
                scene.tick(still)
            self.assertEqual(scene.settings.x, stopped_at)
            self.assertEqual(len(scene.completions), count)

    def test_long_play_follows_both_sides_escalates_and_keeps_head_on_pointer(self):
        for scale in (1, 2):
            with self.subTest(scale=scale):
                scene = CursorTrajectory(scale, friendship=0)
                directions, paces = set(), set()
                first_seen = {}
                previous_x = scene.settings.x
                assert previous_x is not None
                for n in range(400):
                    x, y = scene.eyes()
                    width = 192 * scale
                    point = (round(x + width * 2 * math.cos(n * .25)),
                             round(y - width * (1 + .3 * math.sin(n * .25))))
                    axis = gaze_sector(x, y, *point, scale=scale,
                                       previous=scene.visual.sector)
                    choice = scene.tick(point)
                    clip_name = choice.sprite.animation
                    if scene.coordinator.intent.feeling == "curiosity":
                        if clip_name.startswith("body-step"):
                            clip = scene.runtime._assets.body_clips[clip_name]
                            self.assertEqual(clip.head_direction, axis)
                            self.assertFalse(choice.reverse)
                            paces.add("step")
                            self.assertAlmostEqual(choice.playback_rate, 1)
                        elif clip_name.startswith("running-"):
                            paces.add("run")
                            self.assertIn(axis, (4, 12))
                        elif clip_name == "look":
                            self.assertEqual(choice.sprite.fixed_frame, axis)
                        elif clip_name.startswith("body-look-"):
                            assert axis is not None
                            side = 1 if clip_name.endswith("right") else -1
                            self.assertEqual(choice.sprite.fixed_frame,
                                             body_look_index(side, axis))
                    current_x = scene.settings.x
                    assert current_x is not None
                    delta = current_x - previous_x
                    if delta:
                        directions.add(1 if delta > 0 else -1)
                    previous_x = current_x
                    impression = cursor_impression(scene.state.moodlets)
                    if impression:
                        first_seen.setdefault(impression.level, scene.now)
                self.assertEqual(directions, {-1, 1})
                self.assertEqual(paces, {"step"})
                self.assertEqual([e.level for e in scene.feedback], [1, 2, 3])
                self.assertLess(first_seen[1], first_seen[2])
                self.assertLess(first_seen[2], first_seen[3])
                # Maintenance extends the bounded moodlet without speech spam.
                impression = cursor_impression(scene.state.moodlets)
                assert impression is not None
                self.assertGreater(impression.last_trigger_at, 45)
                stopped_pointer = scene.observer.current.pointer
                for _ in range(700):
                    scene.tick(stopped_pointer)
                self.assertFalse(scene.coordinator.intent.moving)
                self.assertFalse(scene.coordinator.intent.gaze)
                self.assertIsNone(cursor_impression(scene.state.moodlets))
                self.assertEqual(len(scene.feedback), 3)

    def test_foreground_suspends_evidence_and_contact_immediately_pauses(self):
        scene = CursorTrajectory()
        scene.activity = CursorActivityContext(foreground_active=True)
        for _ in range(40):
            scene.tick((820, 194))
        self.assertFalse(scene.feedback)
        self.assertEqual(scene.settings.x, 500)
        scene.activity = CursorActivityContext()
        scene.interest()
        scene.offer_moving_target()
        feedback_before_contact = list(scene.feedback)
        scene.coordinator.claim_access(scene.now)
        scene.walk.clear_cursor_request(scene.now)
        scene.activity = CursorActivityContext(direct_contact=True)
        stopped_at = scene.settings.x
        scene.walk.set_world_goal(900)
        for _ in range(40):
            scene.tick((820, 194))
        self.assertEqual(scene.settings.x, stopped_at)
        self.assertEqual(scene.walk.movement.goal_x, 900)
        self.assertEqual(scene.feedback, feedback_before_contact)

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
