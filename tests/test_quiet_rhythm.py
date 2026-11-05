"""Actual anonymous input, bounded recurrence and simple window learning."""

from __future__ import annotations

import unittest
from datetime import datetime

from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory, Observation
from aiko_pet.pet.mind.quiet_rhythm import QuietPhase, QuietWindow

START = datetime(2026, 10, 12, 23).timestamp()


class QuietRhythmTests(unittest.TestCase):
    def sample(self, routine, seconds, idle, **kwargs):
        return routine.observe_input(
            wall=START + seconds, monotonic=seconds, idle_seconds=idle, **kwargs
        )

    def test_one_jitter_does_not_count_as_return_but_repeated_input_does(self):
        routine = AdaptiveRoutine()
        for seconds in range(0, 1801, 15):
            self.sample(routine, seconds, seconds)
        jitter = self.sample(routine, 1815, 0)
        self.assertEqual(jitter.active_seconds, 0)
        assert jitter.idle_seconds is not None
        self.assertGreaterEqual(jitter.idle_seconds, 900)
        context = jitter
        for seconds in range(1830, 1951, 15):
            context = self.sample(routine, seconds, 0)
        self.assertGreaterEqual(context.active_seconds, 120)
        self.assertEqual(context.idle_seconds, 0)

    def test_old_last_input_changes_cannot_invent_recent_input(self):
        routine = AdaptiveRoutine()
        for seconds in range(0, 3601, 30):
            context = self.sample(routine, seconds, 5000)
            self.assertEqual(context.active_seconds, 0)
        self.assertEqual(routine.memory.quiet_window.phases, ())

    def test_real_quiet_phase_only_records_after_sustained_return(self):
        routine = AdaptiveRoutine()
        for seconds in range(0, 8 * 3600 + 1, 30):
            self.sample(routine, seconds, seconds)
        for seconds in range(8 * 3600 + 30, 8 * 3600 + 151, 30):
            self.sample(routine, seconds, 0)
        self.assertEqual(len(routine.memory.quiet_window.phases), 1)
        phase = routine.memory.quiet_window.phases[0]
        self.assertEqual(phase.start, 1380)
        self.assertEqual(phase.end, 7 * 60)
        for seconds in range(8 * 3600 + 180, 8 * 3600 + 360, 30):
            self.sample(routine, seconds, 0)
        self.assertEqual(len(routine.memory.quiet_window.phases), 1)

    def test_unknown_gap_and_restart_do_not_train_closed_time(self):
        routine = AdaptiveRoutine()
        self.sample(routine, 0, 0)
        for seconds in range(8 * 3600, 8 * 3600 + 151, 30):
            self.sample(routine, seconds, 0)
        self.assertEqual(routine.memory.quiet_window.phases, ())
        restarted = AdaptiveRoutine(routine.memory)
        self.sample(restarted, 16 * 3600, 16 * 3600)
        self.assertEqual(restarted.memory.quiet_window.phases, ())

    def test_host_measured_suspension_is_an_allowed_quiet_phase(self):
        routine = AdaptiveRoutine()
        self.sample(routine, 0, 0)
        self.sample(routine, 8 * 3600, 0, unavailable_seconds=8 * 3600)
        for seconds in range(8 * 3600 + 30, 8 * 3600 + 151, 30):
            self.sample(routine, seconds, 0)
        self.assertEqual(len(routine.memory.quiet_window.phases), 1)

    def test_three_and_seven_phases_and_half_hour_daily_limit(self):
        window = QuietWindow()
        for day in range(1, 8):
            window = window.record(QuietPhase(f"2026-10-{day:02d}", 60, 9 * 60))
            self.assertEqual(window.recurring, day)
            self.assertEqual(window.start, (1380 + min(4, max(0, day - 2)) * 30) % 1440)
        self.assertEqual(window.start, 60)
        self.assertEqual(window.end, 540)
        before = window.start, window.end
        window = window.record(QuietPhase("2026-10-08", 8 * 60, 16 * 60))
        self.assertEqual((window.start, window.end), before)
        self.assertEqual(len(window.phases), 7)

    def test_opposite_day_window_does_not_collapse_during_daily_adjustment(self):
        window = QuietWindow()
        for day in range(1, 29):
            window = window.record(QuietPhase(f"2026-10-{day:02d}", 600, 1200))
            self.assertGreaterEqual((window.end - window.start) % 1440, 240)
            self.assertEqual(QuietWindow.from_dict(window.to_dict()), window)
        self.assertEqual((window.start, window.end), (600, 1200))

    def test_same_day_cannot_count_twice_and_midnight_is_circular(self):
        window = QuietWindow()
        for day, minute in ((1, 1430), (2, 10), (3, 0)):
            window = window.record(QuietPhase(f"2026-10-{day:02d}", minute, 480))
        self.assertEqual(window.recurring, 3)
        self.assertEqual(window.start, 1410)
        self.assertEqual(window.record(QuietPhase("2026-10-03", 480, 960)), window)

    def test_load_manual_commands_and_learning_switch_do_not_train_sleep(self):
        routine = AdaptiveRoutine()
        for seconds in range(0, 8 * 3600 + 1, 30):
            routine.observe(
                Observation(START + seconds, 0.99, seconds),
                seconds,
                energy=8,
                sleeping=True,
                manual_sleep=True,
            )
            self.sample(routine, seconds, seconds, learn=False)
            routine.note_interaction(START + seconds)
        for seconds in range(8 * 3600 + 30, 8 * 3600 + 151, 30):
            self.sample(routine, seconds, 0, learn=False)
        self.assertEqual(routine.memory.quiet_window.phases, ())
        encoded = routine.memory.to_dict()
        restored = AdaptiveMemory.from_dict(encoded)
        self.assertEqual(restored.quiet_window, routine.memory.quiet_window)

    def test_enabling_learning_cannot_retroactively_train_a_disabled_phase(self):
        routine = AdaptiveRoutine()
        for seconds in range(0, 8 * 3600 + 1, 30):
            self.sample(routine, seconds, seconds, learn=False)
        for seconds in range(8 * 3600 + 30, 8 * 3600 + 151, 30):
            self.sample(routine, seconds, 0, learn=True)
        self.assertEqual(routine.memory.quiet_window.phases, ())

    def test_measured_standby_can_extend_an_already_observed_quiet_phase(self):
        routine = AdaptiveRoutine()
        for seconds in range(0, 2 * 3600 + 1, 30):
            self.sample(routine, seconds, seconds)
        self.sample(routine, 5 * 3600, 0, unavailable_seconds=3 * 3600)
        for seconds in range(5 * 3600 + 30, 5 * 3600 + 151, 30):
            self.sample(routine, seconds, 0)
        self.assertEqual(len(routine.memory.quiet_window.phases), 1)
        self.assertEqual(routine.memory.quiet_window.phases[0].start, 1380)

    def test_round_trip_and_forget_preserve_separate_workload_evidence(self):
        routine = AdaptiveRoutine()
        for day in range(1, 8):
            routine.memory.quiet_window = routine.memory.quiet_window.record(
                QuietPhase(f"2026-10-{day:02d}", 1380, 420)
            )
        restored = AdaptiveMemory.from_dict(routine.memory.to_dict())
        self.assertEqual(restored.quiet_window, routine.memory.quiet_window)
        routine.forget_profile()
        self.assertEqual(routine.memory.quiet_window, QuietWindow())
