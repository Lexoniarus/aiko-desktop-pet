"""Session consumption, suspend-safe platform readers and hourly care rhythm."""

from __future__ import annotations

import ctypes
import math
import unittest
from datetime import datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.activity import ActivityCallbacks, ActivityCoordinator
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController, CareRuntime
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.active_time import active_uptime_seconds
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.mind import PetMind
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot

NOW = datetime(2026, 10, 13, 10).timestamp()


class Monitor:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()

    def set_enabled(self, enabled: bool) -> None:
        pass


class ActiveTimeTests(unittest.TestCase):
    def test_intervals_are_consumed_once_and_bad_readings_reset_anchor(self) -> None:
        readings = iter([10., 12., None, 20., 22., 15., 17., math.nan, 25., 26.])
        clock = ActiveSessionClock(lambda: next(readings))
        self.assertEqual([clock.consume() for _ in range(9)],
                         [2, 0, 0, 2, 0, 2, 0, 0, 1])

    def test_windows_reader_uses_unbiased_ticks_and_handles_failure(self) -> None:
        def read(pointer: Any) -> int:
            ctypes.cast(pointer, ctypes.POINTER(ctypes.c_ulonglong))[0] = 10**9
            return 1
        function = MagicMock(side_effect=read)
        dll = SimpleNamespace(kernel32=SimpleNamespace(
            QueryUnbiasedInterruptTime=function,
        ))
        with patch('aiko_pet.infrastructure.active_time.sys.platform', 'win32'), \
                patch('aiko_pet.infrastructure.active_time.ctypes.windll',
                      dll, create=True):
            self.assertEqual(active_uptime_seconds(), 100.)
            function.side_effect = None
            function.return_value = 0
            self.assertIsNone(active_uptime_seconds())

    def test_linux_reader_uses_suspend_excluding_monotonic(self) -> None:
        with patch('aiko_pet.infrastructure.active_time.sys.platform', 'linux'), \
                patch('aiko_pet.infrastructure.active_time.time.CLOCK_MONOTONIC',
                      1, create=True), \
                patch('aiko_pet.infrastructure.active_time.time.clock_gettime',
                      return_value=12., create=True) as reader:
            self.assertEqual(active_uptime_seconds(), 12.)
            reader.assert_called_once_with(1)

    def test_tick_care_and_save_share_one_interval_even_after_wall_jump(self) -> None:
        uptime = [0.]
        clock = ActiveSessionClock(lambda: uptime[0])
        state = PetState(satiety=100, updated_at=NOW)
        mind, adaptive = PetMind(), AdaptiveRoutine()
        activity = ActivityCoordinator(
            state, PetSettings(auto_routine=False), mind, adaptive,
            WorkloadEventDetector(), Monitor(),
            ActivityCallbacks(lambda: None, lambda _: None, lambda *_: None,
                              lambda: 0, lambda: 0), clock=clock,
        )
        care = CareController(state, mind, adaptive, clock=clock)
        uptime[0] = 3600
        activity.advance_state(NOW + 3600)
        care.execute(CareCommand('talk'), CareRuntime(
            NOW + 3600, 3600, False, None, False, False, None,
        ))
        activity.advance_state(NOW + 3600)  # Save at the same instant.
        self.assertAlmostEqual(state.satiety, 92)
        activity.advance_state(NOW + 86400)  # Suspend/clock jump: uptime unchanged.
        self.assertAlmostEqual(state.satiety, 92)
        uptime[0] += 60
        activity.advance_state(NOW + 86460)
        self.assertAlmostEqual(state.satiety, 91.8667, places=3)


class HourlyCareTests(unittest.TestCase):
    def full_state(self) -> PetState:
        return PetState(satiety=100, mood=100, energy=100, social=100,
                        affection=100, updated_at=NOW)

    def test_hourly_targets_with_continuously_observed_load(self) -> None:
        for effort, expected in ((None, 92), (1., 90.4)):
            with self.subTest(effort=effort):
                state = self.full_state()
                for seconds in range(10, 3601, 10):
                    state.advance(NOW + seconds, elapsed_seconds=10, effort=effort)
                self.assertAlmostEqual(state.satiety, expected)
                self.assertGreater(min(state.mood, state.energy, state.social,
                                       state.affection), 90)
                state.interact('feed', now=NOW + 3600)
                self.assertAlmostEqual(state.satiety, 100)

    def test_eight_hour_care_day_stays_playable_and_bond_is_capped(self) -> None:
        state = self.full_state()
        for hour in range(1, 9):
            stamp = NOW + hour * 3600
            state.advance(stamp, elapsed_seconds=3600)
            state.interact('feed', now=stamp)
            if hour % 3 == 0:
                state.interact('talk', now=stamp)
            if hour % 4 == 0:
                state.interact('pet', now=stamp)
                state.interact('play', now=stamp)
            self.assertGreater(min(state.satiety, state.mood, state.energy,
                                   state.social, state.affection), 20)
        self.assertLessEqual(state.friendship, 20)

    def test_sleep_retains_gentle_recovery_and_unknown_load_has_no_bonus(self) -> None:
        state = self.full_state()
        state.sleeping, state.energy = True, 40
        state.advance(NOW + 3600, elapsed_seconds=3600, effort=1.)
        self.assertAlmostEqual(state.energy, 62)
        self.assertAlmostEqual(state.satiety, 98.6)
