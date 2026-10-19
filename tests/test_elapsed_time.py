"""Real-time continuation, source recovery and atomic interval ownership."""

from __future__ import annotations

import math
import unittest
from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from aiko_pet.application.active_time import (
    ActiveSessionClock,
    SessionInputs,
    advance_session_time,
)
from aiko_pet.infrastructure.active_time import elapsed_uptime_seconds
from aiko_pet.pet.food import FoodActivity
from aiko_pet.pet.lifecycle import plan_pet_time
from aiko_pet.pet.state import PetState

NOW = datetime(2026, 10, 12, 12).timestamp()


def inputs(stamp: float) -> SessionInputs:
    return SessionInputs(stamp, 0, False, None, False, False, None)


class ElapsedClockTests(unittest.TestCase):
    def test_windows_uses_suspend_inclusive_ticks(self) -> None:
        function = MagicMock(return_value=40_000_000)
        dll = SimpleNamespace(kernel32=SimpleNamespace(GetTickCount64=function))
        with patch("aiko_pet.infrastructure.active_time.sys.platform", "win32"), \
                patch("aiko_pet.infrastructure.active_time.ctypes.windll",
                      dll, create=True):
            self.assertEqual(elapsed_uptime_seconds(), 40_000)
            self.assertEqual(function.argtypes, [])
            function.side_effect = OSError("unavailable")
            self.assertIsNone(elapsed_uptime_seconds())

    def test_linux_uses_boottime_and_does_not_substitute_active_time(self) -> None:
        with patch("aiko_pet.infrastructure.active_time.sys.platform", "linux"), \
                patch("aiko_pet.infrastructure.active_time.time.CLOCK_BOOTTIME",
                      7, create=True), \
                patch("aiko_pet.infrastructure.active_time.time.clock_gettime",
                      return_value=40_000, create=True) as read:
            self.assertEqual(elapsed_uptime_seconds(), 40_000)
            read.assert_called_once_with(7)
            read.side_effect = OSError("unavailable")
            self.assertIsNone(elapsed_uptime_seconds())

    def test_fallback_and_source_recovery_never_replay_an_interval(self) -> None:
        readings = iter([None, None, 300, 330, None, 400, 410])
        clock = ActiveSessionClock(lambda: next(readings), wall_time=lambda: 0)
        actual = [clock.consume(wall_time=stamp) for stamp in (10, 20, 50, 60, 70, 80)]
        self.assertEqual(actual, [10, 10, 30, 10, 10, 10])
        self.assertEqual(sum(actual), 80)

    def test_uptime_wins_over_forward_and_backward_wall_corrections(self) -> None:
        readings = iter([100, 160, 220, 280])
        clock = ActiveSessionClock(lambda: next(readings), wall_time=lambda: NOW)
        for stamp in (NOW + 86400, NOW - 86400, NOW):
            self.assertEqual(clock.consume(wall_time=stamp), 60)

    def test_backward_fallback_rebases_without_negative_time(self) -> None:
        clock = ActiveSessionClock(lambda: None, wall_time=lambda: NOW)
        self.assertEqual(clock.consume(wall_time=NOW - 3600), 0)
        self.assertEqual(clock.consume(wall_time=NOW - 3540), 60)
        self.assertEqual(clock.consume(wall_time=math.nan), 0)
        self.assertEqual(clock.consume(wall_time=NOW), 0)
        self.assertEqual(clock.consume(wall_time=NOW + 60), 60)


class ElapsedAdvancementTests(unittest.TestCase):
    def test_ten_hour_standby_is_consumed_once_not_limited_to_eight(self) -> None:
        uptime = [100.0]
        clock = ActiveSessionClock(lambda: uptime[0])
        pet = PetState(satiety=100, energy=100, updated_at=NOW)
        uptime[0] += 10 * 3600
        advance_session_time(pet, clock, inputs(NOW + 10 * 3600))
        self.assertEqual(pet.lived_seconds, 10 * 3600)
        self.assertAlmostEqual(pet.energy, 70)
        first = pet.capture_checkpoint()
        advance_session_time(pet, clock, inputs(NOW + 10 * 3600))
        self.assertEqual(pet.capture_checkpoint(), first)

    def test_failed_advancement_rolls_back_pet_and_clock_before_retry(self) -> None:
        uptime = [100.0]
        clock = ActiveSessionClock(lambda: uptime[0])
        pet = PetState(updated_at=NOW)
        checkpoint = pet.capture_checkpoint()
        original = PetState.advance

        def fail_after_mutation(state: PetState, *args: object, **kw: object) -> None:
            original(state, NOW + 60, elapsed_seconds=60)
            raise RuntimeError("interrupted advancement")

        uptime[0] = 160
        with patch.object(PetState, "advance", autospec=True,
                          side_effect=fail_after_mutation):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                advance_session_time(pet, clock, inputs(NOW + 60))
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        uptime[0] = 180
        advance_session_time(pet, clock, inputs(NOW + 80))
        self.assertEqual(pet.lived_seconds, 80)
        self.assertAlmostEqual(pet.energy, 75 - 80 / 3600 * 3)

    def test_invalid_timestamp_does_not_consume_a_valid_uptime_interval(self) -> None:
        uptime = [100.0]
        clock = ActiveSessionClock(lambda: uptime[0])
        pet = PetState(updated_at=NOW)
        uptime[0] += 60
        advance_session_time(pet, clock, inputs(math.nan))
        self.assertEqual(pet.updated_at, NOW)
        advance_session_time(pet, clock, inputs(NOW + 60))
        self.assertEqual(pet.lived_seconds, 60)

    def test_recent_input_and_hardware_are_not_projected_across_standby(self) -> None:
        calm = PetState(satiety=100, energy=100, updated_at=NOW)
        busy = PetState(satiety=100, energy=100, updated_at=NOW)
        for pet, observed in ((calm, FoodActivity()), (busy, FoodActivity(1, 1))):
            uptime = [0.0]
            clock = ActiveSessionClock(lambda: uptime[0])
            uptime[0] = 6 * 3600
            advance_session_time(
                pet, clock,
                replace(inputs(NOW + 6 * 3600), food_activity=observed),
            )
        self.assertGreater(calm.satiety - busy.satiety, 0)
        self.assertLess(calm.satiety - busy.satiety, 0.05)
        self.assertEqual(calm.lived_seconds, busy.lived_seconds)

    def test_long_routine_plan_streams_the_entire_duration(self) -> None:
        duration = 30 * 86400
        plan = plan_pet_time(NOW, NOW + duration, auto_routine=True)
        assert plan is not None
        self.assertNotIsInstance(plan, (tuple, list))
        self.assertAlmostEqual(sum(step.hours for step in plan), duration / 3600)
        pet = PetState(updated_at=NOW)
        pet.advance(NOW + duration, auto_routine=True)
        self.assertEqual(pet.lived_seconds, duration)
        self.assertEqual(pet.friendship, 15)  # No new relationship model yet.
        self.assertIsNone(pet.food.last_food_id)

    def test_current_activity_flags_do_not_cancel_unobserved_night_sleep(self) -> None:
        start = datetime(2026, 10, 12, 19).timestamp()
        end = datetime(2026, 10, 13, 10).timestamp()
        historical = PetState(updated_at=start, energy=0)
        returned_user = PetState(updated_at=start, energy=0)
        historical.advance(end, auto_routine=True)
        returned_user.advance(end, auto_routine=True, allow_bedtime=False)
        self.assertGreater(returned_user.energy, 50)
        self.assertEqual(returned_user.energy, historical.energy)


if __name__ == "__main__":
    unittest.main()
