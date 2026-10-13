"""Headless tests for the independent resting and glance director."""

from __future__ import annotations

import unittest

from aiko_pet.presentation.ambient import AmbientDirector
from aiko_pet.presentation.animation import SpriteSelection


class AmbientDirectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = AmbientDirector(
            100.0, between=lambda low, _high: low,
            direction=lambda options: options[0],
        )

    def test_idle_rest_never_restarts_blink_in_the_same_beat(self) -> None:
        self.assertEqual(self.policy.choose(100), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(105), SpriteSelection("idle"))
        self.assertTrue(self.policy.blinking)
        self.assertEqual(self.policy.choose(106), SpriteSelection("idle"))
        self.policy.finish_blink(108)
        self.assertFalse(self.policy.blinking)
        self.assertEqual(self.policy.choose(109), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(110), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(111), SpriteSelection("idle"))

    def test_blink_gaps_allow_three_to_eight_seconds(self) -> None:
        self.assertEqual(self.policy.next_blink_at, 103.0)
        self.assertEqual(self.policy.choose(102.99), SpriteSelection("idle", 0))
        self.assertEqual(self.policy.choose(103), SpriteSelection("idle"))
        self.policy.finish_blink(104.28)
        self.assertEqual(self.policy.next_blink_at, 107.28)

        longest = AmbientDirector(
            100.0, between=lambda _low, high: high,
            direction=lambda options: options[0],
        )
        self.assertEqual(longest.next_blink_at, 108.0)
        longest.suspend(200.0)
        self.assertEqual(longest.next_blink_at, 208.0)

    def test_independent_glance_uses_one_static_direction_then_rests(self) -> None:
        self.policy.next_blink_at = 1000.0
        self.assertEqual(
            self.policy.choose(122), SpriteSelection("look", fixed_frame=2),
        )
        self.assertEqual(
            self.policy.choose(123), SpriteSelection("look", fixed_frame=2),
        )
        self.assertEqual(self.policy.choose(124), SpriteSelection("idle", 0))
        self.assertGreater(self.policy.next_glance_at, 124)

    def test_suspension_clears_spontaneous_activity(self) -> None:
        self.policy.choose(105)
        self.assertTrue(self.policy.blinking)
        self.policy.suspend(105.2)
        self.assertFalse(self.policy.blinking)
        self.assertEqual(
            self.policy.choose(105.2), SpriteSelection("idle", 0),
        )
        self.assertGreater(self.policy.next_blink_at, 105.2)
        self.assertGreater(self.policy.next_glance_at, 105.2)

    def test_slow_motion_continues_during_neutral_rest(self) -> None:
        offsets = [
            self.policy.motion_offset(100 + index * .42 + .01)
            for index in range(9)
        ]
        self.assertEqual(offsets, [0, 0, 1, 1, 0, 0, -1, -1, 0])
        self.assertLessEqual(max(map(abs, offsets)), 1)

    def test_current_gaze_keeps_motion_clock_while_actions_reset_it(self) -> None:
        self.policy.suspend(101, keep_pose_motion=True)
        self.assertEqual(self.policy.motion_offset(101), 1)
        self.policy.suspend(101)
        self.assertEqual(self.policy.motion_offset(101), 0)
        self.assertEqual(self.policy.motion_offset(101 + .85), 1)
        self.policy.next_blink_at = 103
        self.policy.choose(105)
        self.assertTrue(self.policy.blinking)
        self.policy.finish_blink(105.2)
        self.assertEqual(self.policy.motion_offset(105.2), 0)

    def test_invalid_autonomous_direction_is_rejected(self) -> None:
        bad = AmbientDirector(
            0.0, between=lambda low, _high: low,
            direction=lambda _options: 16,
        )
        with self.assertRaises(ValueError):
            bad.choose(22)


if __name__ == "__main__":
    unittest.main()
