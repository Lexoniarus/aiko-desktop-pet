"""Headless regression tests for walking and sprite frame decisions."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.presentation.animation import (
    FrameClock,
    SpriteSelection,
    choose_passive_animation,
)
from aiko_pet.presentation.movement import WalkConditions, WalkController
from aiko_pet.desktop.geometry import TaskbarTrack


class FrameClockTests(unittest.TestCase):
    def test_authored_durations_and_exact_boundaries(self) -> None:
        clock = FrameClock()
        timings = (280, 110, 60, 50, 70, 70, 140, 320)
        self.assertEqual(clock.next_index("idle", 10, timings), 0)
        self.assertEqual(clock.next_index("idle", 10.279, timings), 0)
        self.assertEqual(clock.next_index("idle", 10.28, timings), 1)
        self.assertEqual(clock.next_delay_ms, 110)
        self.assertEqual(clock.next_index("idle", 10.389, timings), 1)
        self.assertEqual(clock.next_index("idle", 10.39, timings), 2)
        self.assertEqual(clock.next_index("idle", 10.45, timings), 3)
        self.assertEqual(clock.next_delay_ms, 50)

    def test_delayed_callbacks_show_all_eight_walking_frames(self) -> None:
        clock = FrameClock()
        timings = (120,) * 7 + (220,)
        observed = [clock.next_index("running-right", 0, timings)]
        for index in range(1, 8):
            now = clock.frame_started_at + timings[index - 1] / 1000 + .15
            observed.append(clock.next_index("running-right", now, timings))
            self.assertEqual(clock.next_delay_ms, timings[index])
        self.assertEqual(observed, list(range(8)))
        now = clock.frame_started_at + .22
        self.assertEqual(clock.next_index("running-right", now, timings), 0)

    def test_one_shot_holds_every_frame_and_extends_a_late_deadline(self) -> None:
        clock = FrameClock()
        self.assertEqual(clock.next_index("eat", 0, (200, 300), loop=False), 0)
        self.assertAlmostEqual(clock.end_time, .5)
        self.assertEqual(clock.next_index("eat", .5, (200, 300), loop=False), 1)
        self.assertFalse(clock.finished)
        self.assertAlmostEqual(clock.end_time, .8)
        self.assertEqual(clock.next_index("eat", .799, (200, 300), loop=False), 1)
        self.assertFalse(clock.finished)
        self.assertEqual(clock.next_index("eat", .8, (200, 300), loop=False), 1)
        self.assertTrue(clock.finished)
        self.assertIsNone(clock.next_delay_ms)
        clock.reset()
        self.assertEqual(clock.next_index("eat", 10, (200, 300), loop=False), 0)
        self.assertFalse(clock.finished)

    def test_fixed_gaze_and_switch_reset_animation(self) -> None:
        clock = FrameClock()
        clock.next_index("idle", 1, (280, 110))
        self.assertEqual(clock.next_index("look", 2, (1000,) * 16, fixed=14), 14)
        self.assertIsNone(clock.next_delay_ms)
        self.assertEqual(clock.next_index("look", 8, (1000,) * 16, fixed=14), 14)
        self.assertEqual(clock.next_index("idle", 8, (280, 110)), 0)

    def test_invalid_durations_and_fixed_index(self) -> None:
        clock = FrameClock()
        for timings in ((), (0,), (-1, 30)):
            with self.assertRaises(ValueError):
                clock.next_index("idle", 0, timings)
        with self.assertRaises(IndexError):
            clock.next_index("look", 0, (1000,) * 16, fixed=16)

    def test_motion_progress_tracks_shown_frames_during_late_callbacks(self) -> None:
        clock = FrameClock()
        timings = (160,) * 7 + (293,)
        clock.next_index('running-right', 0, timings)
        self.assertAlmostEqual(clock.progress_seconds(.5, timings), .16)
        clock.next_index('running-right', .5, timings)
        self.assertAlmostEqual(clock.progress_seconds(.5, timings), .16)
        now = .5
        for duration in timings[1:]:
            now = clock.frame_started_at + duration / 1000 + .1
            before = clock.progress_seconds(now, timings)
            clock.next_index('running-right', now, timings)
            self.assertAlmostEqual(clock.progress_seconds(now, timings), before)
        self.assertEqual(clock.frame_index, 0)
        self.assertAlmostEqual(clock.progress_seconds(now, timings), 1.413)


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
            speed_pixels_per_second=68 / 1.413, stride_pixels=68,
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
        self.assertTrue(self.walker.record_displacement(2.0, now=15))
        self.assertEqual(self.walker.remaining_distance, 0.0)

    def test_walk_left_and_stop_at_clamped_screen_edge(self) -> None:
        self.walker.remaining_distance = -10
        step = self.walker.plan_step(self.conditions(x=0))
        assert step is not None
        self.assertEqual(step.animation, "running-left")
        self.assertLess(step.pixels, 0)
        self.assertTrue(self.walker.record_displacement(0, now=15, blocked=True))
        self.assertEqual(self.walker.remaining_distance, 0)

    def test_bursts_are_bounded_by_elapsed_time(self) -> None:
        self.walker.remaining_distance = 100
        first = self.walker.plan_step(self.conditions(elapsed_seconds=0.25))
        second = self.walker.plan_step(self.conditions(elapsed_seconds=0))
        assert first is not None
        assert second is not None
        self.assertAlmostEqual(first.pixels, 68 / 1.413 * .25)
        self.assertEqual(second.pixels, 0)

    def test_work_delays_next_walk_and_cancels_movement(self) -> None:
        self.walker.remaining_distance = 100
        self.assertIsNone(self.walker.plan_step(
            self.conditions(observing_computer=True, computer_busy=True),
        ))
        self.assertEqual(self.walker.remaining_distance, 0)
        with patch("aiko_pet.presentation.movement.random.uniform", return_value=90):
            self.assertIsNone(self.walker.plan_step(self.conditions(now=100)))
        self.assertEqual(self.walker.next_walk_at, 190)

    def test_hover_and_manual_disabled_walk_cancel_distance(self) -> None:
        for settings in ({"toolbar_visible": True}, {"auto_walk": False},
                         {"attention_active": True}, {"sleeping": True}):
            with self.subTest(settings=settings):
                self.walker.remaining_distance = 100
                self.assertIsNone(self.walker.plan_step(self.conditions(**settings)))
                self.assertEqual(self.walker.remaining_distance, 0)

    def test_energy_defers_walk_but_sets_next_departure(self) -> None:
        with patch("aiko_pet.presentation.movement.random.uniform", return_value=90):
            self.assertIsNone(self.walker.plan_step(self.conditions(energy=19)))
        self.assertEqual(self.walker.next_walk_at, 105)
        self.assertEqual(self.walker.remaining_distance, 0)

    def test_edge_direction_and_quiet_interval(self) -> None:
        with (
            patch("aiko_pet.presentation.movement.random.uniform", return_value=20),
            patch("aiko_pet.presentation.movement.random.randint", return_value=2),
        ):
            step = self.walker.plan_step(self.conditions(x=0, quiet_period=True))
        assert step is not None
        self.assertEqual(step.animation, "running-right")
        self.assertEqual(self.walker.remaining_distance, 136)
        self.assertEqual(self.walker.next_walk_at, float("inf"))

    def test_subpixel_motion_survives_short_callbacks_in_both_directions(self) -> None:
        for direction in (-1, 1):
            with self.subTest(direction=direction):
                walker = WalkController(next_walk_at=100)
                walker.remaining_distance = 100 * direction
                x = 300
                for n in range(250):
                    step = walker.plan_step(self.conditions(
                        now=n * .004, elapsed_seconds=.004, x=x,
                    ))
                    assert step is not None
                    new_x = round(x + step.pixels)
                    self.assertFalse(walker.record_displacement(
                        new_x - x, now=n * .004,
                    ))
                    x = new_x
                self.assertAlmostEqual(abs(x - 300), 68 / 1.413, delta=.5)
                self.assertGreater(abs(walker.remaining_distance), 50)

    def test_complete_pause_starts_at_actual_finish_even_after_long_walk(self) -> None:
        self.walker.remaining_distance = 2
        self.walker.plan_step(self.conditions(now=100))
        with patch("aiko_pet.presentation.movement.random.uniform", return_value=90):
            self.assertTrue(self.walker.record_displacement(2, now=100))
        self.assertEqual(self.walker.next_walk_at, 190)
        self.assertIsNone(self.walker.plan_step(self.conditions(now=189)))

    def test_brief_pointer_attention_does_not_restart_an_idle_pause(self) -> None:
        self.assertIsNone(self.walker.plan_step(self.conditions(
            now=9, attention_active=True,
        )))
        self.assertEqual(self.walker.next_walk_at, 10)
        self.assertIsNotNone(self.walker.plan_step(self.conditions(now=15)))


if __name__ == "__main__":
    unittest.main()
