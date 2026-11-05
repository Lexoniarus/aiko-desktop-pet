"""Cursor attention changes must preserve existing walking deferrals."""

import unittest
from dataclasses import replace

from aiko_pet.pet.mind.cursor_attention import CursorAttention, CursorPerception


class CursorAttentionTests(unittest.TestCase):
    def test_first_position_only_establishes_a_baseline(self) -> None:
        tracker = CursorAttention()
        self.assertFalse(tracker.observe((20, 30), 1.0))
        self.assertEqual(tracker.previous_pointer, (20, 30))
        self.assertEqual(tracker.last_pointer_move, -100.0)

    def test_motion_starts_only_one_attention_pulse_per_six_seconds(self) -> None:
        tracker = CursorAttention()
        tracker.observe((1, 1), 100.0)
        self.assertTrue(tracker.observe((2, 1), 101.0))
        self.assertEqual(tracker.attention_until, 102.0)
        self.assertFalse(tracker.observe((2, 1), 103.0))
        self.assertTrue(tracker.observe((3, 1), 104.0))
        self.assertEqual(tracker.last_pointer_move, 104.0)
        self.assertEqual(tracker.attention_until, 102.0)
        self.assertTrue(tracker.observe((4, 1), 108.0))
        self.assertEqual(tracker.attention_until, 109.0)

    def test_game_mode_preserves_baseline_without_reacting(self) -> None:
        tracker = CursorAttention()
        tracker.observe((1, 1), 50.0)
        self.assertFalse(tracker.observe((20, 30), 51.0, game_mode=True))
        self.assertEqual(tracker.previous_pointer, (20, 30))
        self.assertEqual(tracker.last_pointer_move, -100.0)
        self.assertTrue(tracker.observe((21, 30), 52.0))
        tracker.reset()
        self.assertIsNone(tracker.previous_pointer)
        self.assertEqual(tracker.attention_until, -100.0)


class MotionBandTests(unittest.TestCase):
    def test_exact_band_boundaries_and_stationary_override(self):
        for speed, band in ((0, "slow"), (.499, "slow"), (.5, "normal"),
                            (1.499, "normal"), (1.5, "fast"), (2.999, "fast"),
                            (3, "very_fast"), (9, "very_fast")):
            p = CursorPerception(speed=speed)
            self.assertEqual(p.motion_band, band)
            self.assertEqual(replace(p, stationary_seconds=.3).motion_band, "still")

    def test_filter_is_time_weighted_and_gaps_do_not_make_velocity(self):
        for dt in (.1, .2):
            tracker = CursorAttention()
            tracker.observe((0, 0), 0)
            tracker.observe((round(100 * dt), 0), dt)
            import math
            self.assertAlmostEqual(tracker.velocity[0], 100 * (1 - math.exp(-dt / .3)))
            tracker.observe((10000, 0), 10)
            self.assertFalse(tracker.valid)
            self.assertEqual(tracker.velocity, (0, 0))
