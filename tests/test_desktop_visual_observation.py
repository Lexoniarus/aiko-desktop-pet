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
    def setUp(self) -> None:
        self.settings = PetSettings()
        self.monitor = Monitor()
        self.observer = DesktopVisualObservation(
            settings=self.settings, monitor=self.monitor,
            eyes=lambda: (100.0, 200.0),
        )

    def test_pointer_gaze_suppresses_unneeded_monitor_reading(self) -> None:
        observation = self.observer.observe(
            101.0, (100, 0), 100.0, game_mode=False,
        )
        self.assertEqual(observation, PassiveObservation(0, False))
        self.assertEqual(self.monitor.calls, 0)
        self.assertEqual(self.observer.sector, 0)

    def test_stale_pointer_clears_gaze_and_uses_cached_workload(self) -> None:
        self.observer.gaze_direction((100, 0))
        observation = self.observer.observe(
            110.0, (100, 0), 100.0, game_mode=False,
        )
        self.assertEqual(observation, PassiveObservation(None, True))
        self.assertIsNone(self.observer.sector)
        self.assertEqual(self.monitor.calls, 1)

    def test_cursor_disabled_still_observes_machine_when_enabled(self) -> None:
        self.settings.follow_cursor = False
        observation = self.observer.observe(
            101.0, (100, 0), 100.0, game_mode=False,
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
            settings=self.settings, monitor=self.monitor,
            eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(
                phase=lambda: phase, walking=lambda: walking,
                sleeping=lambda: sleeping,
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
            self.assertFalse(attention.sees_environment(.1, 0))
            sleeping = True
            self.assertEqual(observer.observe(1, pointer, 0, False),
                             PassiveObservation(None, False))
            self.assertIsNone(observer.sector)
            phase, walking, sleeping = "idle", 0, False
            self.settings.follow_cursor = True
            observer.object_target = None

    def test_activity_port_holds_perception_across_cursor_and_movement(self):
        active = True
        observer = DesktopVisualObservation(
            settings=self.settings, monitor=self.monitor, eyes=lambda: (100, 200),
            attention=VisualAttentionPorts(activity_active=lambda: active,
                                           walking=lambda: 10),
        )
        self.assertEqual(observer.attention((300, 200), pointer_recent=True).mode,
                         "unavailable")
        active = False
        self.assertEqual(observer.attention((300, 200), pointer_recent=True).mode,
                         "moving")
