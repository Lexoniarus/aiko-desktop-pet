"""Headless tests for the adaptive mode and sleep decision policies."""

import unittest
from datetime import datetime

from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory, Observation
from aiko_pet.pet.mind.adaptive_policy import (
    ActivityMode,
    SleepOptions,
    determine_activity_mode,
    determine_sleep_options,
)


def mode(
    *,
    effort: float | None = 0.1,
    settled_work: float = 0.1,
    last_session_seconds: float = 0.0,
    last_work_wall: float = 0.0,
    rest_seconds: float = 0.0,
    present: bool | None = None,
    wall_time: float = 1000.0,
) -> ActivityMode:
    return determine_activity_mode(
        effort=effort, settled_work=settled_work,
        last_session_seconds=last_session_seconds,
        last_work_wall=last_work_wall, rest_seconds=rest_seconds,
        present=present, wall_time=wall_time,
    )


def sleep(
    *,
    mode: ActivityMode = "present",
    energy: float = 75.0,
    sleeping: bool = False,
    manual_sleep: bool = False,
    night: bool = False,
    effort: float | None = 0.1,
    idle_seconds: float | None = 0.0,
    present: bool | None = True,
    rest_seconds: float = 0.0,
    expected_effort: float | None = None,
) -> SleepOptions:
    return determine_sleep_options(
        mode=mode, energy=energy, sleeping=sleeping,
        manual_sleep=manual_sleep, night=night, effort=effort,
        idle_seconds=idle_seconds, present=present,
        rest_seconds=rest_seconds, expected_effort=expected_effort,
    )


class ActivityModeTests(unittest.TestCase):
    def test_busy_effort_outranks_everything(self) -> None:
        self.assertEqual(
            mode(effort=0.8, last_session_seconds=500, rest_seconds=1000),
            "working",
        )
        self.assertEqual(mode(effort=0.4, settled_work=0.6), "working")

    def test_recovery_requires_recent_observed_work(self) -> None:
        self.assertEqual(
            mode(last_session_seconds=120, last_work_wall=900), "recovering",
        )
        self.assertEqual(
            mode(last_session_seconds=120, last_work_wall=800), "wandering",
        )
        self.assertEqual(
            mode(last_session_seconds=119, last_work_wall=900), "wandering",
        )

    def test_rest_present_and_wandering_are_distinct(self) -> None:
        self.assertEqual(mode(rest_seconds=300, present=True), "resting")
        self.assertEqual(mode(rest_seconds=299, present=True), "present")
        self.assertEqual(mode(present=None, effort=None), "wandering")


class AdaptiveSleepTests(unittest.TestCase):
    def test_night_quiet_prefers_sleep_but_work_never_does(self) -> None:
        self.assertTrue(
            sleep(night=True, idle_seconds=200, present=False).can_sleep,
        )
        self.assertFalse(
            sleep(mode="working", night=True, effort=0.9).can_sleep,
        )

    def test_manual_sleep_is_not_interrupted(self) -> None:
        self.assertFalse(
            sleep(sleeping=True, manual_sleep=True, mode="working").should_wake,
        )
        self.assertTrue(
            sleep(sleeping=True, manual_sleep=False, mode="working").should_wake,
        )
        self.assertTrue(
            sleep(sleeping=True, present=True, night=False).should_wake,
        )

    def test_nap_requires_observed_rest_and_low_energy(self) -> None:
        self.assertTrue(
            sleep(
                energy=18, present=False, idle_seconds=1000,
                rest_seconds=900,
            ).can_nap,
        )
        self.assertFalse(
            sleep(energy=18, present=None, rest_seconds=900).can_nap,
        )
        self.assertTrue(
            sleep(
                energy=35, present=False,
                rest_seconds=900, expected_effort=0.31,
            ).can_nap,
        )
        self.assertFalse(
            sleep(
                energy=35, present=False,
                rest_seconds=900, expected_effort=0.32,
            ).can_nap,
        )

    def test_day_and_night_thresholds_remain_independent(self) -> None:
        self.assertTrue(sleep(energy=23, rest_seconds=1800).can_sleep)
        self.assertFalse(sleep(energy=24, rest_seconds=1800).can_sleep)
        self.assertFalse(sleep(energy=75, night=False).can_sleep)


class AdaptiveRoutineBoundaryTests(unittest.TestCase):
    def test_unknown_load_does_not_fabricate_session_time(self) -> None:
        stamp = datetime(2026, 10, 12, 10).timestamp()
        memory = AdaptiveMemory()
        adaptive = AdaptiveRoutine(memory)
        first = adaptive.observe(
            Observation(stamp, None, None, uptime_hours=42),
            100.0, energy=75, sleeping=False,
        )
        self.assertEqual(first.mode, "wandering")
        second = adaptive.observe(
            Observation(stamp + 10, None, None, uptime_hours=42),
            110.0, energy=75, sleeping=False,
        )
        self.assertEqual(second.mode, "wandering")
        self.assertEqual(memory.session_seconds, 0)
        self.assertEqual(sum(memory.hour_seconds), 0)

    def test_suspend_gap_does_not_count_unseen_work(self) -> None:
        stamp = datetime(2026, 10, 12, 10).timestamp()
        adaptive = AdaptiveRoutine()
        adaptive.observe(
            Observation(stamp, 0.95, 0),
            10.0, energy=80, sleeping=False,
        )
        adaptive.observe(
            Observation(stamp + 7200, 0.95, 0),
            7210.0, energy=80, sleeping=False,
        )
        self.assertEqual(adaptive.memory.session_seconds, 0)


if __name__ == "__main__":
    unittest.main()
