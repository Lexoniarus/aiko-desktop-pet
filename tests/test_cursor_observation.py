"""Mouse observations share PetMind's clock but need no Tk window."""

import unittest

from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.pet.mind.cursor_attention import CursorAttention


class CursorObservationTests(unittest.TestCase):
    def test_stationary_samples_accumulate_time_without_motion(self) -> None:
        result = None
        for i in range(12):
            result = self.observer.observe(
                (250, 160),
                i * 0.14,
                game_mode=False,
                eyes=(100, 82),
                screen_width=1920,
            )
        assert result is not None
        self.assertIsNone(result.motion)
        self.assertGreater(result.perception.stationary_seconds, 1.5)
        self.assertTrue(result.perception.reachable)

    def test_velocity_is_normalized_and_distinguishes_approach(self) -> None:
        readings = []
        for scale in (1, 2):
            observer = CursorObservation(CursorAttention())
            result = None
            for i in range(4):
                result = observer.observe(
                    ((400 - i * 30) * scale, 80 * scale),
                    i * 0.14,
                    game_mode=False,
                    eyes=(100 * scale, 80 * scale),
                    screen_width=1920,
                    scale=scale,
                )
            assert result is not None
            readings.append(result.perception)
        self.assertAlmostEqual(readings[0].speed, readings[1].speed)
        self.assertAlmostEqual(readings[0].distance, readings[1].distance)
        self.assertGreater(readings[0].closing_speed, 0)

    def test_own_motion_and_sample_gap_do_not_invent_mouse_attack(self) -> None:
        result = None
        for i in range(4):
            result = self.observer.observe(
                (400, 160),
                i * 0.14,
                game_mode=False,
                eyes=(100 + i * 25, 82),
                screen_width=1920,
            )
        assert result is not None
        self.assertEqual(result.perception.speed, 0)
        result = self.observer.observe(
            (10, 160),
            100,
            game_mode=False,
            eyes=(100, 82),
            screen_width=1920,
        )
        self.assertFalse(result.perception.valid)
        assert result is not None
        self.assertEqual(result.perception.speed, 0)

    def test_fast_motion_away_and_passing_have_no_closing_threat(self) -> None:
        for start, finish in [((250, 82), (350, 82)), ((250, 82), (250, 182))]:
            observer = CursorObservation(CursorAttention())
            observer.observe(
                start, 0, game_mode=False, eyes=(100, 82), screen_width=1920
            )
            result = observer.observe(
                finish, 0.14, game_mode=False, eyes=(100, 82), screen_width=1920
            )
            self.assertLessEqual(result.perception.closing_speed, 0)

    def setUp(self) -> None:
        self.clock = CursorAttention()
        self.observer = CursorObservation(self.clock)

    def test_first_sample_does_not_emit_motion(self) -> None:
        result = self.observer.observe(
            (10, 20),
            900,
            game_mode=False,
            eyes=(96, 82),
            screen_width=1920,
        )
        assert result is not None
        self.assertIsNone(result.motion)
        self.assertEqual(self.clock.previous_pointer, (10, 20))

    def test_moving_pointer_produces_original_distance_and_screen(self) -> None:
        self.observer.observe(
            (10, 20),
            900,
            game_mode=False,
            eyes=(96, 82),
            screen_width=1920,
        )
        result = self.observer.observe(
            (99999, -99999),
            1000,
            game_mode=False,
            eyes=(96, 82),
            screen_width=1920,
        )
        assert result.motion is not None
        result = result.motion
        self.assertGreater(result.distance, result.screen_width * 0.6)
        self.assertEqual((result.now, result.screen_width), (1000, 1920))
        self.assertEqual(self.clock.last_pointer_move, 1000)
        self.assertEqual(self.clock.snapshot().attention_until, 1001)

    def test_game_mode_only_refreshes_pointer_baseline(self) -> None:
        self.assertIsNone(
            self.observer.observe(
                (10, 20),
                100,
                game_mode=True,
                eyes=(0, 0),
                screen_width=1920,
            ).motion
        )
        self.assertIsNone(
            self.observer.observe(
                (20, 30),
                101,
                game_mode=True,
                eyes=(0, 0),
                screen_width=1920,
            ).motion
        )
        self.assertEqual(self.clock.previous_pointer, (20, 30))
        self.assertEqual(self.clock.last_pointer_move, -100)
        self.assertIsNotNone(
            self.observer.observe(
                (21, 30),
                102,
                game_mode=False,
                eyes=(0, 0),
                screen_width=1920,
            ).motion
        )

    def test_snapshot_has_no_write_access_to_clock(self) -> None:
        copy = self.clock.snapshot()
        self.assertEqual(copy.last_pointer_move, -100)
        self.clock.observe((1, 2), 1)
        self.clock.observe((3, 4), 2)
        self.assertEqual(copy.last_pointer_move, -100)
        self.assertEqual(self.clock.snapshot().last_pointer_move, 2)
