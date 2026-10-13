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
        self.assertEqual(self.policy.choose(113), SpriteSelection("idle"))

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

    def test_invalid_autonomous_direction_is_rejected(self) -> None:
        bad = AmbientDirector(
            0.0, between=lambda low, _high: low,
            direction=lambda _options: 16,
        )
        with self.assertRaises(ValueError):
            bad.choose(22)


if __name__ == "__main__":
    unittest.main()
