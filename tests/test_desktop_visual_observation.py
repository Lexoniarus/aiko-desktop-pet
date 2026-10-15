"""Native observation and gaze decisions do not belong to the sprite."""

from __future__ import annotations

import unittest

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.visual_observation import DesktopVisualObservation
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
