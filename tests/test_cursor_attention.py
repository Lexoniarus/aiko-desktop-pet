"""Cursor attention changes must preserve existing walking deferrals."""

import unittest

from aiko_pet.pet.mind.cursor_attention import CursorAttention


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
