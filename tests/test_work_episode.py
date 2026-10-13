"""Headless contract tests for Aiko's observed work-episode memory."""

from __future__ import annotations

import unittest

from aiko_pet.adaptive_models import Behaviour
from aiko_pet.work_episode import WorkEpisodeMemory


def scene(
    *, mode: str = "working", duration: float = 150.0,
    confidence: bool = False, expectation: float | None = None,
) -> Behaviour:
    # The observed activity mode is a test fixture, never a made-up history.
    from aiko_pet.adaptive_policy import ActivityMode
    from typing import cast

    return Behaviour(
        mode=cast(ActivityMode, mode), strain=35.0, effort=0.8,
        expected_effort=expectation, expectation_confident=confidence,
        present=True, uptime_hours=24.0,
        prolonged_work_seconds=duration, rest_seconds=0.0,
        can_sleep=False, should_wake=False, can_nap=False,
    )


class WorkEpisodeMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.memory = WorkEpisodeMemory()

    def test_observed_interrupted_work_has_one_recovery_payoff(self) -> None:
        busy = scene(duration=150.0)
        resting = scene(mode="recovering", duration=0.0)
        self.memory.observe(None, busy, now=20.0)
        self.memory.note_click(busy)
        self.memory.note_click(busy)
        self.memory.observe(busy, resting, now=41.0)
        self.assertTrue(self.memory.recovering(41.0))
        self.assertEqual(
            self.memory.interpret_event(
                "computer_effort_recovered_peak", resting, 41.0,
            ),
            "work_finished_interrupted",
        )
        self.assertEqual(self.memory.interruptions, 0)
        self.assertEqual(
            self.memory.interpret_event(
                "computer_effort_recovered", resting, 42.0,
            ),
            "computer_effort_recovered",
        )
        self.assertFalse(self.memory.recovering(153.0))

    def test_long_work_reflects_once_inside_bounded_window(self) -> None:
        busy = scene(duration=2600.0)
        resting = scene(mode="resting", duration=0.0)
        self.memory.observe(None, busy, now=400.0)
        self.memory.observe(busy, resting, now=500.0)
        self.assertFalse(self.memory.take_postwork_thought(559.0))
        self.assertTrue(self.memory.take_postwork_thought(560.0))
        self.assertFalse(self.memory.take_postwork_thought(570.0))
        self.assertFalse(self.memory.take_postwork_thought(981.0))
        self.assertEqual(
            self.memory.interpret_event(
                "computer_effort_recovered", resting, 1000.0,
            ),
            "work_finished_long",
        )

    def test_missing_reading_discards_interruptions_not_invents_work(self) -> None:
        busy = scene(duration=250.0)
        self.memory.observe(None, busy, now=100.0)
        self.memory.note_click(busy)
        self.memory.note_click(busy)
        self.memory.observe(busy, None, now=110.0)
        self.assertEqual(self.memory.interruptions, 0)
        self.assertFalse(self.memory.recovering(111.0))
        self.assertEqual(self.memory.last_work_duration, 0.0)

    def test_new_work_episode_resets_previous_interruptions(self) -> None:
        busy = scene()
        idle = scene(mode="resting", duration=0.0)
        self.memory.observe(None, busy, now=10.0)
        self.memory.note_click(busy)
        self.memory.observe(busy, idle, now=20.0)
        self.memory.observe(idle, busy, now=30.0)
        self.assertEqual(self.memory.interruptions, 0)
        self.assertFalse(self.memory.recovering(31.0))
        self.memory.note_click(idle)
        self.assertEqual(self.memory.interruptions, 0)

    def test_short_peak_does_not_become_long_work(self) -> None:
        busy = scene(duration=8.0)
        resting = scene(mode="recovering", duration=0.0)
        self.memory.observe(None, busy, now=100.0)
        self.memory.note_click(busy)
        self.memory.note_click(busy)
        self.memory.observe(busy, resting, now=108.0)
        self.assertEqual(
            self.memory.interpret_event(
                "computer_effort_recovered", resting, 109.0,
            ),
            "computer_effort_recovered",
        )
        self.assertFalse(self.memory.take_postwork_thought(210.0))

    def test_unexpected_work_needs_confident_observed_profile(self) -> None:
        self.assertEqual(
            self.memory.interpret_event(
                "computer_effort_heavy",
                scene(confidence=True, expectation=0.09), 100.0,
            ),
            "work_unexpected",
        )
        self.assertEqual(
            self.memory.interpret_event(
                "computer_effort_heavy",
                scene(confidence=False, expectation=0.09), 101.0,
            ),
            "computer_effort_heavy",
        )
        self.assertEqual(
            self.memory.interpret_event("computer_effort_heavy", None, 102.0),
            "computer_effort_heavy",
        )


if __name__ == "__main__":
    unittest.main()
