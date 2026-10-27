"""Explicit whole-body plans preserve full frontal head freedom."""

import unittest

from aiko_pet.pet.animation.animation import SpriteSelection
from aiko_pet.pet.animation.body_orientation import BodyOrientation, body_look_index
from aiko_pet.pet.mind.cursor_behaviour import BodyIntent


class BodyOrientationTests(unittest.TestCase):
    def setUp(self):
        self.body = BodyOrientation()

    def pose(self, now, direction=4, side=0, intent: BodyIntent = "front"):
        return self.body.select(
            now, SpriteSelection("look", direction), intent=intent, side=side
        )

    def orient_right(self):
        for i in range(4):
            self.pose(i * 0.14, side=1, intent="three_quarter")

    def test_all_sixteen_frontal_directions_never_turn_even_after_long_wait(self):
        for direction in range(16):
            for now in (0, 2, 100):
                self.assertEqual(
                    self.pose(now, direction), SpriteSelection("look", direction)
                )
                self.assertEqual(self.body.phase, 0)

    def test_explicit_turn_preserves_each_step_and_independent_head(self):
        actual = [self.pose(i * 0.14, side=1, intent="three_quarter") for i in range(4)]
        self.assertEqual(
            actual,
            [SpriteSelection("body-turn-right", n) for n in (1, 2, 3)]
            + [SpriteSelection("body-look-right", 4)],
        )
        self.assertEqual(
            self.pose(0.56, 2, 1, "three_quarter"),
            SpriteSelection("body-look-right", 2),
        )

    def test_opposite_head_is_clamped_until_explicit_side_change_returns_front(self):
        self.orient_right()
        self.assertEqual(
            self.pose(0.56, 12, 1, "three_quarter"),
            SpriteSelection("body-look-right", 4),
        )
        actual = [self.pose(0.7 + i * 0.14, 12, -1, "three_quarter") for i in range(5)]
        self.assertEqual(
            actual,
            [SpriteSelection("body-turn-right", n) for n in (3, 2, 1)]
            + [SpriteSelection("look", 12), SpriteSelection("body-turn-left", 1)],
        )

    def test_idle_returns_in_order_and_restores_original_blink(self):
        self.orient_right()
        idle = SpriteSelection("idle")
        actual = [self.body.select(0.56 + i * 0.14, idle) for i in range(4)]
        self.assertEqual(actual[-1], idle)
        self.assertEqual([s.fixed_frame for s in actual[:-1]], [3, 2, 1])

    def test_late_ticks_do_not_skip_authored_turn_steps(self):
        self.assertEqual(self.pose(10, 12, -1, "three_quarter").fixed_frame, 1)
        self.assertEqual(self.pose(20, 12, -1, "three_quarter").fixed_frame, 2)

    def test_profile_hold_and_return_have_all_existing_whole_poses(self):
        poses = [self.pose(i * 0.14, side=1, intent="profile") for i in range(9)]
        self.assertEqual([p.fixed_frame for p in poses], list(range(1, 9)) + [8])
        phases = [self.pose(1.4 + i * 0.14).fixed_frame for i in range(8)]
        self.assertEqual(phases[:7], list(range(7, 0, -1)))
        self.assertEqual(self.body.phase, 0)

    def test_active_visuals_reset_and_impossible_body_look_is_rejected(self):
        self.orient_right()
        choice = SpriteSelection("sleep")
        self.assertEqual(self.body.select(1, choice), choice)
        self.assertEqual(self.body.phase, 0)
        for side, head in ((1, 12), (-1, 4)):
            with self.assertRaises(ValueError):
                body_look_index(side, head)


class MotionOrientationTests(unittest.TestCase):
    def test_profile_ready_only_after_all_turn_poses_and_return_is_ordered(self):
        body = BodyOrientation()
        phases = []
        for i in range(8):
            pose = body.orient_for_motion(i * 0.14, 1)
            phases.append(pose.fixed_frame)
            self.assertEqual(body.motion_ready, i == 7)
        self.assertEqual(phases, list(range(1, 9)))
        pose = body.select(1.12, SpriteSelection("idle"))
        self.assertEqual(pose.fixed_frame, 7)
