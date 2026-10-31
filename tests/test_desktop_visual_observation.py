"""Native observation and gaze decisions do not belong to the sprite."""

from __future__ import annotations

import unittest

from aiko_pet.application.object_feedback import InteractionPhase
from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.visual_observation import (
    DesktopVisualObservation,
    VisualAttentionPorts,
)
from aiko_pet.pet.animation.animation import PassiveObservation
from aiko_pet.pet.mind.cursor_behaviour import CursorIntent
from aiko_pet.pet.mind.object_attention import LookSide


class Reading:
    def is_busy(self) -> bool:
        return True


class Monitor:
    def __init__(self) -> None:
        self.calls = 0

    def latest(self) -> Reading:
        self.calls += 1
        return Reading()


class DesktopVisualObservationTests(unittest.TestCase):
    def test_world_attention_reads_actual_body_until_front_is_reached(self):
        from aiko_pet.pet.animation.animation import SpriteSelection
        from aiko_pet.pet.animation.body_orientation import BodyOrientation

        body = BodyOrientation()
        self.observer.constrain_with(body.constrain_direction)
        for n in range(4):
            body.select(n * .14, SpriteSelection("look", 4),
                        intent="three_quarter", side=1)
        self.selected = CursorIntent("observe", target=(-400, 200))
        attention = self.observer.attention((-400, 200), pointer_recent=True)
        assert attention.direction is not None
        self.assertGreater(attention.direction[0], 0)
        self.assertFalse(attention.sees_environment(-400, -200))
        for n in range(4):
            body.select(.56 + n * .14, SpriteSelection("look", 12))
        attention = self.observer.attention((-400, 200), pointer_recent=True)
        assert attention.direction is not None
        self.assertLess(attention.direction[0], 0)
        self.assertTrue(attention.sees_environment(-400, -200))

    def test_desired_cursor_axis_does_not_grant_world_sight_before_actual_front(self):
        from aiko_pet.pet.animation.body_orientation import BodyOrientation

        body = BodyOrientation()
        body.orient_for_gaze_motion(0, 3)
        body.orient_for_gaze_motion(.07, 3)
        self.observer.constrain_with(body.constrain_direction)
        self.selected = CursorIntent("approach", side=-1, target=(-400, 100),
                                     feeling="curiosity")
        before = self.observer.sector
        self.assertEqual(self.observer.desired_cursor_gaze(), 13)
        self.assertEqual(self.observer.sector, before)
        actual = self.observer.attention((-400, 100), pointer_recent=True)
        assert actual.direction is not None
        self.assertGreater(actual.direction[0], 0)
        self.assertEqual((body.phase, body.side), (8, 1))
        body.reset()
        actual = self.observer.attention((-400, 100), pointer_recent=True)
        assert actual.direction is not None
        self.assertLess(actual.direction[0], 0)

    def test_step_uses_compatible_cursor_axis_for_perception_and_head(self):
        point = (250, 150)
        observer = DesktopVisualObservation(
            settings=PetSettings(),
            monitor=Monitor(),
            eyes=lambda: (100.0, 200.0),
            attention=VisualAttentionPorts(
                walking=lambda: 10,
                walk_kind=lambda: "step",
                cursor_intent=lambda: CursorIntent("observe", target=point),
            ),
        )
        self.assertEqual(observer.observe(100, (250, 150), 99, False).gaze_direction, 3)
        point = (-100, 150)
        self.assertEqual(
            observer.observe(100, (-100, 150), 99, False).gaze_direction, 4
        )

    def setUp(self) -> None:
        self.selected = CursorIntent("observe", target=(100, 0))
        self.settings = PetSettings()
        self.monitor = Monitor()
        self.observer = DesktopVisualObservation(
            settings=self.settings,
            monitor=self.monitor,
            eyes=lambda: (100.0, 200.0),
            attention=VisualAttentionPorts(cursor_intent=lambda: self.selected),
        )

    def test_pointer_gaze_suppresses_unneeded_monitor_reading(self) -> None:
        observation = self.observer.observe(
            101.0,
            (100, 0),
            100.0,
            game_mode=False,
        )
        self.assertEqual(observation, PassiveObservation(0, False))
        self.assertEqual(self.monitor.calls, 0)
        self.assertEqual(self.observer.sector, 0)

    def test_stale_pointer_clears_gaze_and_uses_cached_workload(self) -> None:
        self.observer.gaze_direction((100, 0))
        self.selected = CursorIntent()
        observation = self.observer.observe(
            110.0,
            (100, 0),
            100.0,
            game_mode=False,
        )
        self.assertEqual(observation, PassiveObservation(None, True))
        self.assertIsNone(self.observer.sector)
        self.assertEqual(self.monitor.calls, 1)

    def test_cursor_disabled_still_observes_machine_when_enabled(self) -> None:
        self.settings.follow_cursor = False
        observation = self.observer.observe(
            101.0,
            (100, 0),
            100.0,
            game_mode=False,
        )
        self.assertEqual(observation, PassiveObservation(None, True))
        self.assertEqual(self.monitor.calls, 1)

    def test_game_mode_suppresses_gaze_and_hardware(self) -> None:
        self.observer.gaze_direction((100, 0))
        self.assertIsNone(
            self.observer.gaze_direction((100, 0), game_mode=True),
        )
        self.assertEqual(
            self.observer.observe(101.0, (100, 0), 100.0, game_mode=True),
            PassiveObservation(None, False),
        )
        self.assertEqual(self.monitor.calls, 0)
        self.assertIsNone(self.observer.sector)

    def test_observation_disabled_never_reads_hardware(self) -> None:
        self.settings.follow_cursor = False
        self.settings.observe_computer = False
        self.assertEqual(
            self.observer.observe(101.0, (100, 0), 100.0, game_mode=False),
            PassiveObservation(None, False),
        )
        self.assertEqual(self.monitor.calls, 0)

    def test_live_attention_uses_eye_geometry_and_existing_action_owners(self):
        phase: InteractionPhase = "idle"
        walking = 0.0
        sleeping = False
        observer = DesktopVisualObservation(
            settings=self.settings,
            monitor=self.monitor,
            eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(
                phase=lambda: phase,
                walking=lambda: walking,
                sleeping=lambda: sleeping,
                cursor_intent=lambda: CursorIntent("observe", target=pointer),
            ),
        )
        for scale in (1, 2):
            self.settings.scale = scale
            width = 192 * scale
            pointer = (100 + 3 * width, 200 - width)
            attention = observer.attention(pointer, pointer_recent=True)
            self.assertEqual(attention.mode, "cursor")
            self.assertEqual(attention.direction, (3, 1))
            observer.object_target = (100 - 3 * width, 200)
            self.settings.follow_cursor = False
            self.assertEqual(observer.observe(1, pointer, 0, False).gaze_direction, 12)
            walking = 10
            self.assertEqual(observer.observe(1, pointer, 0, False).gaze_direction, 4)
            phase = "inspect"
            attention = observer.attention(pointer, pointer_recent=True)
            self.assertEqual(attention.mode, "object")
            self.assertFalse(attention.sees_environment(0.1, 0))
            sleeping = True
            self.assertEqual(
                observer.observe(1, pointer, 0, False), PassiveObservation(None, False)
            )
            self.assertIsNone(observer.sector)
            phase, walking, sleeping = "idle", 0, False
            self.settings.follow_cursor = True
            observer.object_target = None

    def test_activity_port_holds_perception_across_cursor_and_movement(self):
        active = True
        observer = DesktopVisualObservation(
            settings=self.settings,
            monitor=self.monitor,
            eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(
                activity_active=lambda: active, walking=lambda: 10
            ),
        )
        self.assertEqual(
            observer.attention((300, 200), pointer_recent=True).mode, "unavailable"
        )
        active = False
        self.assertEqual(
            observer.attention((300, 200), pointer_recent=True).mode, "moving"
        )

    def test_only_feedback_for_the_live_tracked_subject_keeps_its_focus(self):
        followed, feedback = "known", "known"
        observer = DesktopVisualObservation(
            settings=self.settings,
            monitor=self.monitor,
            eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(
                following_subject=lambda: followed,
                feedback_subject=lambda: feedback,
                activity_active=lambda: True,
            ),
        )
        self.assertEqual(
            observer.attention((300, 200), pointer_recent=True).mode, "object"
        )
        feedback = "another"
        self.assertEqual(
            observer.attention((300, 200), pointer_recent=True).mode, "unavailable"
        )
        followed = None
        self.assertEqual(
            observer.attention((300, 200), pointer_recent=True).mode, "unavailable"
        )

    def test_orientation_read_port_controls_actual_gaze_before_sensor_sampling(self):
        side: LookSide = -1
        observer = DesktopVisualObservation(
            settings=self.settings,
            monitor=self.monitor,
            eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(orientation_side=lambda: side),
        )
        observer.object_target = (1000, 200)
        self.assertTrue(observer.orienting)
        self.assertEqual(
            observer.attention((100, 0), pointer_recent=True).direction, (-1, 0)
        )
        self.assertEqual(observer.gaze_direction((100, 0)), 12)
        side = 1
        self.assertEqual(observer.gaze_direction((100, 0)), 4)

    def test_raw_pointer_does_not_replace_selected_attention(self):
        self.selected = CursorIntent("observe", target=(100, 0))
        raw = (-1000, 200)
        before = self.observer.attention(raw, pointer_recent=True)
        self.assertEqual(before.direction, (0, 200 / 192))
        self.assertEqual(self.observer.observe(101, raw, 101, False).gaze_direction, 0)
        self.selected = CursorIntent()
        self.assertEqual(
            self.observer.attention(raw, pointer_recent=True).mode, "survey"
        )
