"""Mouse observations share PetMind's clock but need no Tk window."""

import unittest

from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.pet.mind.cursor_attention import CursorAttention


class CursorObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = CursorAttention()
        self.observer = CursorObservation(self.clock)

    def test_first_sample_does_not_emit_motion(self) -> None:
        result = self.observer.observe(
            (10, 20), 900, game_mode=False, eyes=(96, 82),
            screen_width=1920,
        )
        self.assertIsNone(result)
        self.assertEqual(self.clock.previous_pointer, (10, 20))

    def test_moving_pointer_produces_original_distance_and_screen(self) -> None:
        self.observer.observe(
            (10, 20), 900, game_mode=False, eyes=(96, 82),
            screen_width=1920,
        )
        result = self.observer.observe(
            (99999, -99999), 1000, game_mode=False, eyes=(96, 82),
            screen_width=1920,
        )
        assert result is not None
        self.assertGreater(result.distance, result.screen_width * .6)
        self.assertEqual((result.now, result.screen_width), (1000, 1920))
        self.assertEqual(self.clock.last_pointer_move, 1000)
        self.assertEqual(self.clock.snapshot().attention_until, 1001)

    def test_game_mode_only_refreshes_pointer_baseline(self) -> None:
        self.assertIsNone(self.observer.observe(
            (10, 20), 100, game_mode=True, eyes=(0, 0),
            screen_width=1920,
        ))
        self.assertIsNone(self.observer.observe(
            (20, 30), 101, game_mode=True, eyes=(0, 0),
            screen_width=1920,
        ))
        self.assertEqual(self.clock.previous_pointer, (20, 30))
        self.assertEqual(self.clock.last_pointer_move, -100)
        self.assertIsNotNone(self.observer.observe(
            (21, 30), 102, game_mode=False, eyes=(0, 0),
            screen_width=1920,
        ))

    def test_snapshot_has_no_write_access_to_clock(self) -> None:
        copy = self.clock.snapshot()
        self.assertEqual(copy.last_pointer_move, -100)
        self.clock.observe((1, 2), 1)
        self.clock.observe((3, 4), 2)
        self.assertEqual(copy.last_pointer_move, -100)
        self.assertEqual(self.clock.snapshot().last_pointer_move, 2)
