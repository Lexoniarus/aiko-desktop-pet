"""Whole-body gaze turns preserve attention and return through frontal."""

from __future__ import annotations

import unittest

from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.body_orientation import BodyOrientation, body_look_index


class BodyOrientationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.body = BodyOrientation()

    def look(self, at: float, direction: int) -> SpriteSelection:
        return self.body.select(at, SpriteSelection("look", direction))

    def orient_right(self) -> None:
        for at in (0, 1.20, 1.34, 1.48, 1.62):
            self.look(at, 4)

    def test_brief_pointer_glances_only_move_head(self) -> None:
        self.assertEqual(self.look(0, 4), SpriteSelection("look", 4))
        self.assertEqual(self.look(0.14, 12), SpriteSelection("look", 12))
        self.assertEqual(self.look(0.28, 4), SpriteSelection("look", 4))
        self.assertEqual(self.body.phase, 0)

    def test_sustained_look_uses_each_existing_step_then_independent_head(self):
        self.assertEqual(self.look(0, 4), SpriteSelection("look", 4))
        self.assertEqual(self.look(1.19, 4), SpriteSelection("look", 4))
        actual = [self.look(t, 4) for t in (1.20, 1.34, 1.48, 1.62)]
        self.assertEqual(
            actual,
            [
                SpriteSelection("body-turn-right", 1),
                SpriteSelection("body-turn-right", 2),
                SpriteSelection("body-turn-right", 3),
                SpriteSelection("body-look-right", 4),
            ],
        )
        self.assertEqual(self.look(1.76, 5), SpriteSelection("body-look-right", 5))

    def test_diagonal_glances_turn_after_same_dwell_as_horizontal(self) -> None:
        for direction in (1, 2, 6, 7, 9, 10, 14, 15):
            self.body.reset()
            for at in (0, 0.3, 0.6, 0.9):
                self.assertEqual(
                    self.look(at, direction),
                    SpriteSelection("look", direction),
                )
            side = "right" if direction < 8 else "left"
            self.assertEqual(
                self.look(1.2, direction),
                SpriteSelection(f"body-turn-{side}", 1),
            )

    def test_head_sector_changes_on_same_side_do_not_reset_dwell(self) -> None:
        for at, direction in ((0, 1), (0.4, 3), (0.8, 6)):
            self.assertEqual(
                self.look(at, direction),
                SpriteSelection("look", direction),
            )
        self.assertEqual(self.look(1.2, 7), SpriteSelection("body-turn-right", 1))

    def test_diagonal_change_on_current_side_keeps_body_orientation(self):
        self.orient_right()
        self.assertEqual(self.look(1.76, 2), SpriteSelection("body-look-right", 2))

    def test_fast_alternating_mouse_never_turns_frontal_body(self) -> None:
        for index in range(30):
            direction = 4 if index % 2 else 12
            self.assertEqual(
                self.look(index * 0.1, direction),
                SpriteSelection("look", direction),
            )
            self.assertEqual(self.body.phase, 0)

    def test_brief_opposite_flick_does_not_reverse_already_turned_body(self):
        self.orient_right()
        for at in (1.76, 1.90):
            self.assertEqual(self.look(at, 12), SpriteSelection("body-look-right", 4))
        self.assertEqual(self.look(2.04, 4), SpriteSelection("body-look-right", 4))

    def test_side_change_returns_through_center_before_opposite_look(self):
        self.orient_right()
        self.assertEqual(self.look(1.76, 12), SpriteSelection("body-look-right", 4))
        actual = [self.look(t, 12) for t in (2.96, 3.10, 3.24, 3.38, 3.52)]
        self.assertEqual(
            actual,
            [
                SpriteSelection("body-turn-right", 3),
                SpriteSelection("body-turn-right", 2),
                SpriteSelection("body-turn-right", 1),
                SpriteSelection("look", 12),
                SpriteSelection("body-turn-left", 1),
            ],
        )

    def test_neutral_idle_returns_with_steps_and_preserves_blink_selection(self):
        self.orient_right()
        idle = SpriteSelection("idle")
        actual = [self.body.select(t, idle) for t in (1.76, 1.90, 2.04, 2.18)]
        self.assertEqual(actual[-1], idle)
        self.assertEqual([s.fixed_frame for s in actual[:-1]], [3, 2, 1])

    def test_vertical_gaze_eventually_restores_frontal_default(self) -> None:
        self.orient_right()
        self.assertEqual(self.look(1.76, 0), SpriteSelection("body-look-right", 0))
        self.assertEqual(self.look(1.90, 8), SpriteSelection("body-look-right", 8))
        self.assertEqual(self.look(2.96, 8), SpriteSelection("body-turn-right", 3))

    def test_vertical_gaze_starts_and_stays_frontal(self) -> None:
        for at, direction in ((0, 0), (0.7, 8), (1.4, 0), (2.1, 8)):
            self.assertEqual(
                self.look(at, direction),
                SpriteSelection("look", direction),
            )
            self.assertEqual(self.body.phase, 0)

    def test_late_tick_does_not_skip_authored_turning_steps(self) -> None:
        self.look(0, 12)
        self.assertEqual(self.look(10, 12), SpriteSelection("body-turn-left", 1))
        self.assertEqual(self.look(20, 12), SpriteSelection("body-turn-left", 2))

    def test_active_visuals_reset_orientation_without_world_motion(self) -> None:
        self.orient_right()
        for name in ("sleep", "eat", "pick_up", "running-right", "review"):
            choice = SpriteSelection(name)
            self.assertEqual(self.body.select(1, choice), choice)
            self.assertEqual(self.body.phase, 0)

    def test_opposite_head_direction_is_not_available_on_turned_body(self):
        with self.assertRaises(ValueError):
            body_look_index(1, 12)
        with self.assertRaises(ValueError):
            body_look_index(-1, 4)


class MotionOrientationTests(unittest.TestCase):
    def test_profile_ready_only_after_all_turn_poses_and_return_is_ordered(self):
        from aiko_pet.pet.animation.animation import SpriteSelection
        from aiko_pet.pet.animation.body_orientation import BodyOrientation

        body = BodyOrientation()
        phases = []
        for i in range(8):
            pose = body.orient_for_motion(i * 0.14, 1)
            phases.append(pose.fixed_frame)
            self.assertEqual(body.motion_ready, i == 7)
        self.assertEqual(phases, list(range(1, 9)))
        pose = body.select(1.12, SpriteSelection("idle"))
        self.assertEqual(pose.fixed_frame, 7)
