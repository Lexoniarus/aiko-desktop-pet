"""Headless regression tests for walking and sprite frame decisions."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.pet.animation.animation import (
    FrameClock,
    SpriteSelection,
    choose_passive_animation,
)
from aiko_pet.pet.movement import WalkConditions, WalkController


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


class CurrentClipPacingTests(unittest.TestCase):
    def test_each_clip_plays_all_authored_steps_in_order(self) -> None:
        from aiko_pet.infrastructure.character_assets import (
            load_character_catalog,
        )

        catalog = load_character_catalog()
        self.assertEqual(len(catalog.clips), 16)
        for name, clip in catalog.clips.items():
            if name == "look":
                self.assertEqual(len(clip.frames), 16)
                self.assertEqual(len(clip.timings), 16)
                continue
            with self.subTest(clip=name):
                self.assertEqual(len(clip.frames), 8)
                self.assertGreaterEqual(len(clip.timings), 8)
                self.assertEqual(len(clip.timings), len(clip.playback_order))
                clock = FrameClock()
                self.assertEqual(
                    clock.next_index(name, 0, clip.timings, loop=clip.loop),
                    0,
                )
                for index in range(1, len(clip.timings)):
                    now = (clock.frame_started_at
                           + clip.timings[index - 1] / 1000)
                    self.assertEqual(
                        clock.next_index(name, now, clip.timings,
                                         loop=clip.loop),
                        index,
                    )
                    self.assertEqual(
                        clock.next_delay_ms, clip.timings[index],
                    )
                    self.assertTrue(
                        0 <= clip.sprite_index(index) < len(clip.frames),
                    )
                end = (clock.frame_started_at
                       + clip.timings[-1] / 1000)
                last = clock.next_index(
                    name, end, clip.timings, loop=clip.loop,
                )
                if clip.loop:
                    self.assertEqual(last, 0)
                    self.assertFalse(clock.finished)
                    self.assertEqual(
                        clock.next_delay_ms, clip.timings[0],
                    )
                else:
                    self.assertEqual(last, len(clip.timings) - 1)
                    self.assertTrue(clock.finished)
                    self.assertIsNone(clock.next_delay_ms)

    def test_waving_reuses_all_eight_pngs_for_two_waves(self) -> None:
        from aiko_pet.infrastructure.character_assets import (
            load_character_catalog,
        )

        catalog = load_character_catalog().clips
        ordinary = catalog["waving"]
        greeting = catalog["waving-greeting"]
        self.assertEqual(ordinary.playback_order, tuple(range(8)))
        self.assertEqual(len(ordinary.timings), 8)
        self.assertAlmostEqual(ordinary.duration_seconds, 1.135)
        self.assertEqual(
            greeting.playback_order,
            (0, 1, 2, 3, 4, 5, 4, 3, 4, 5, 4, 3, 6, 7),
        )
        self.assertIs(ordinary.frames, greeting.frames)
        self.assertFalse(greeting.loop)
        self.assertEqual(len(greeting.frames), 8)
        self.assertAlmostEqual(greeting.duration_seconds, 1.895)
        self.assertEqual(greeting.sprite_index(8), 4)
        self.assertEqual(greeting.sprite_index(13), 7)

    def test_idle_and_attack_keep_original_playback(self) -> None:
        from aiko_pet.infrastructure.character_assets import (
            load_character_catalog,
        )

        clips = load_character_catalog().clips
        self.assertEqual(clips["idle"].timings, (160,) * 8)
        self.assertEqual(clips["attack"].timings, (215,) * 8)
        for name in ("idle", "attack"):
            self.assertEqual(clips[name].playback_order, tuple(range(8)))

    def test_delayed_callback_never_skips_a_frame(self) -> None:
        clock = FrameClock()
        timings = (160,) * 8
        self.assertEqual(clock.next_index("waving", 0, timings), 0)
        self.assertEqual(clock.next_index("waving", .8, timings), 1)
        self.assertEqual(clock.next_delay_ms, 160)


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
            speed_pixels_per_second=68 / 1.28, stride_pixels=68,
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
        self.assertAlmostEqual(first.pixels, 68 / 1.28 * .25)
        self.assertEqual(second.pixels, 0)

    def test_work_delays_next_walk_and_cancels_movement(self) -> None:
        self.walker.remaining_distance = 100
        self.assertIsNone(self.walker.plan_step(
            self.conditions(observing_computer=True, computer_busy=True),
        ))
        self.assertEqual(self.walker.remaining_distance, 0)
        with patch("aiko_pet.pet.movement.random_walk.random.uniform", return_value=90):
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
        with patch("aiko_pet.pet.movement.random_walk.random.uniform", return_value=90):
            self.assertIsNone(self.walker.plan_step(self.conditions(energy=19)))
        self.assertEqual(self.walker.next_walk_at, 105)
        self.assertEqual(self.walker.remaining_distance, 0)

    def test_edge_direction_and_quiet_interval(self) -> None:
        with (
            patch("aiko_pet.pet.movement.random_walk.random.uniform", return_value=20),
            patch("aiko_pet.pet.movement.random_walk.random.randint", return_value=2),
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
                self.assertAlmostEqual(abs(x - 300), 68 / 1.28, delta=.5)
                # New 1.28s walking cycles cover 53.125 px in one second.
                self.assertAlmostEqual(
                    abs(walker.remaining_distance), 100 - 68 / 1.28,
                    delta=1.0,
                )

    def test_complete_pause_starts_at_actual_finish_even_after_long_walk(self) -> None:
        self.walker.remaining_distance = 2
        self.walker.plan_step(self.conditions(now=100))
        with patch("aiko_pet.pet.movement.random_walk.random.uniform", return_value=90):
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
