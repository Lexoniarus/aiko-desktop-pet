"""Small autonomous steps retain one rest schedule and existing blockers."""

import unittest
from dataclasses import replace
from unittest.mock import patch

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.pet.movement.contracts import WalkConditions
from aiko_pet.pet.movement.controller import WalkController


class IdleStepTests(unittest.TestCase):
    def setUp(self):
        self.walk = WalkController(next_walk_at=10)
        self.conditions = WalkConditions(
            10,
            0.1,
            30,
            68,
            300,
            TaskbarTrack(0, 1000, 600),
            192,
            80,
            True,
            False,
            False,
            False,
            False,
            False,
            False,
            small_idle_steps=True,
        )

    def test_idle_makes_one_small_step_then_rests(self):
        with (
            patch("aiko_pet.pet.movement.random_walk.random.choice", return_value=1),
            patch("aiko_pet.pet.movement.random_walk.random.random", return_value=0.8),
        ):
            step = self.walk.plan_step(self.conditions)
        assert step is not None
        self.assertEqual(step.kind, "step")
        self.assertEqual(self.walk.remaining_distance, 16)
        self.walk.record_displacement(16, now=11)
        self.assertGreaterEqual(self.walk.next_walk_at, 56)
        self.assertLessEqual(self.walk.next_walk_at, 101)

    def test_attention_sleep_and_controls_take_priority(self):
        for flags in [
            {"attention_active": True},
            {"sleeping": True},
            {"menu_engaged": True},
        ]:
            self.assertIsNone(self.walk.plan_step(replace(self.conditions, **flags)))

    def test_steps_scale_with_sprite_and_turn_away_from_edge(self):
        with patch("aiko_pet.pet.movement.random_walk.random.random", return_value=0.8):
            step = self.walk.plan_step(replace(self.conditions, x=0, sprite_width=384))
        assert step is not None
        self.assertEqual(step.direction, 1)
        self.assertEqual(self.walk.remaining_distance, 32)

    def test_missing_step_package_stays_put_and_does_not_run(self):
        self.assertIsNone(
            self.walk.plan_step(replace(self.conditions, small_idle_steps=False))
        )
        self.assertEqual(self.walk.remaining_distance, 0)
        self.assertGreaterEqual(self.walk.next_walk_at, 55)

    def test_occasional_two_steps_remain_bounded(self):
        with patch("aiko_pet.pet.movement.random_walk.random.random", return_value=0.1):
            self.walk.plan_step(replace(self.conditions, x=0))
        self.assertEqual(self.walk.remaining_distance, 32)
