"""Headless regression tests for walking and sprite frame decisions."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.animation import (
    FrameClock,
    SpriteSelection,
    choose_passive_animation,
)
from aiko_pet.movement import WalkConditions, WalkController
from aiko_pet.taskbar import TaskbarTrack


class FrameClockTests(unittest.TestCase):
    def test_first_frame_and_exact_timing_boundary(self) -> None:
        clock = FrameClock(started_at=0)
        self.assertEqual(clock.next_index("idle", 10, 6), 0)
        self.assertEqual(clock.next_index("idle", 10.379, 6), 0)
        self.assertEqual(clock.next_index("idle", 10.38, 6), 1)

    def test_long_pause_advances_single_frame_and_wraps(self) -> None:
        clock = FrameClock()
        self.assertEqual(clock.next_index("running-right", 0, 2), 0)
        self.assertEqual(clock.next_index("running-right", 30, 2), 1)
        self.assertEqual(clock.next_index("running-right", 30.14, 2), 0)

    def test_fixed_gaze_and_switch_reset_animation(self) -> None:
        clock = FrameClock()
        clock.next_index("idle", 1, 6)
        clock.next_index("idle", 2, 6)
        self.assertEqual(clock.next_index("look", 2, 16, fixed=14), 14)
        self.assertEqual(clock.next_index("look", 8, 16, fixed=14), 14)
        self.assertEqual(clock.next_index("idle", 8, 6), 0)

    def test_invalid_frame_count_and_fixed_index(self) -> None:
        clock = FrameClock()
        with self.assertRaises(ValueError):
            clock.next_index("idle", 0, 0)
        with self.assertRaises(IndexError):
            clock.next_index("look", 0, 16, fixed=16)


class PassiveAnimationTests(unittest.TestCase):
    def select(
        self, *,
        gaze_direction: int | None = None,
        observing_computer: bool = False,
        computer_busy: bool = False,
        energy: float = 75.0,
        mood: float = 75.0,
        satiety: float = 75.0,
    ) -> SpriteSelection:
        return choose_passive_animation(
            gaze_direction=gaze_direction,
            observing_computer=observing_computer,
            computer_busy=computer_busy,
            energy=energy, mood=mood, satiety=satiety,
        )

    def test_gaze_overrides_busy_and_low_needs(self) -> None:
        self.assertEqual(
            self.select(
                gaze_direction=3, observing_computer=True,
                computer_busy=True, energy=0, mood=0, satiety=0,
            ),
            SpriteSelection("look", fixed_frame=3),
        )

    def test_busy_state_requires_observation(self) -> None:
        self.assertEqual(
            self.select(observing_computer=True, computer_busy=True).animation,
            "review",
        )
        self.assertEqual(self.select(computer_busy=True).animation, "idle")

    def test_urgent_needs_take_priority_over_waiting(self) -> None:
        self.assertEqual(self.select(energy=9, satiety=0).animation, "failed")
        self.assertEqual(self.select(mood=9, satiety=0).animation, "failed")
        self.assertEqual(self.select(energy=23).animation, "waiting")
        self.assertEqual(self.select(satiety=19).animation, "waiting")
        self.assertEqual(self.select(energy=24, satiety=20).animation, "idle")


class WalkControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.walker = WalkController(next_walk_at=10)
        self.track = TaskbarTrack(left=0, right=800, ground_y=800)

    def conditions(self, **overrides: object) -> WalkConditions:
        defaults = WalkConditions(
            now=15.0, elapsed_seconds=0.25, x=300,
            track=self.track, sprite_width=128, energy=80,
            auto_walk=True, sleeping=False, attention_active=False,
            toolbar_visible=False, observing_computer=False,
            computer_busy=False, quiet_period=False,
        )
        return replace(defaults, **overrides)

    def test_walk_right_and_complete_using_actual_displacement(self) -> None:
        self.walker.remaining_distance = 2.0
        step = self.walker.plan_step(self.conditions())
        assert step is not None
        self.assertEqual(step.animation, "running-right")
        self.assertEqual(step.pixels, 2.0)
        self.assertTrue(self.walker.record_displacement(2.0))
        self.assertEqual(self.walker.remaining_distance, 0.0)

    def test_walk_left_and_stop_at_clamped_screen_edge(self) -> None:
        self.walker.remaining_distance = -10
        step = self.walker.plan_step(self.conditions(x=0))
        assert step is not None
        self.assertEqual(step.animation, "running-left")
        self.assertLess(step.pixels, 0)
        self.assertTrue(self.walker.record_displacement(0))
        self.assertEqual(self.walker.remaining_distance, 0)

    def test_bursts_are_bounded_by_elapsed_time(self) -> None:
        self.walker.remaining_distance = 100
        first = self.walker.plan_step(self.conditions(elapsed_seconds=0.25))
        second = self.walker.plan_step(self.conditions(elapsed_seconds=0))
        assert first is not None
        assert second is not None
        self.assertEqual(first.pixels, 16)
        self.assertEqual(second.pixels, 1)

    def test_work_delays_next_walk_and_cancels_movement(self) -> None:
        self.walker.remaining_distance = 100
        self.assertIsNone(self.walker.plan_step(
            self.conditions(observing_computer=True, computer_busy=True),
        ))
        self.assertEqual(self.walker.remaining_distance, 0)
        self.assertEqual(self.walker.next_walk_at, 17)

    def test_hover_and_manual_disabled_walk_cancel_distance(self) -> None:
        for settings in ({"toolbar_visible": True}, {"auto_walk": False},
                         {"attention_active": True}, {"sleeping": True}):
            with self.subTest(settings=settings):
                self.walker.remaining_distance = 100
                self.assertIsNone(self.walker.plan_step(self.conditions(**settings)))
                self.assertEqual(self.walker.remaining_distance, 0)

    def test_energy_defers_walk_but_sets_next_departure(self) -> None:
        with patch("aiko_pet.movement.random.uniform", return_value=6):
            self.assertIsNone(self.walker.plan_step(self.conditions(energy=19)))
        self.assertEqual(self.walker.next_walk_at, 21)
        self.assertEqual(self.walker.remaining_distance, 0)

    def test_edge_direction_and_quiet_interval(self) -> None:
        with patch("aiko_pet.movement.random.uniform", return_value=20), patch(
            "aiko_pet.movement.random.randint", return_value=100,
        ):
            step = self.walker.plan_step(self.conditions(x=0, quiet_period=True))
        assert step is not None
        self.assertEqual(step.animation, "running-right")
        self.assertEqual(self.walker.remaining_distance, 100)
        self.assertEqual(self.walker.next_walk_at, 35)


if __name__ == "__main__":
    unittest.main()
