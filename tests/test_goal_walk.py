"""Object goals share motion execution and respect all non-random blockers."""

import unittest
from dataclasses import replace

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.pet.movement.contracts import WalkConditions
from aiko_pet.pet.movement.controller import WalkController


class GoalWalkTests(unittest.TestCase):
    def conditions(self):
        return WalkConditions(
            now=0, elapsed_seconds=1, speed_pixels_per_second=20,
            stride_pixels=68, x=100, track=TaskbarTrack(0, 800, 600),
            sprite_width=192, energy=75, auto_walk=False, sleeping=False,
            attention_active=False, toolbar_visible=False, observing_computer=False,
            computer_busy=False, quiet_period=False,
        )

    def test_goal_moves_without_random_walk_and_uses_actual_displacement(self):
        controller = WalkController(next_walk_at=999)
        controller.set_goal(140)
        step = controller.plan_step(self.conditions())
        assert step is not None
        self.assertEqual(step.pixels, 20)
        controller.record_displacement(20, now=1)
        final = controller.plan_step(replace(self.conditions(), now=1, x=120))
        assert final is not None
        self.assertEqual(final.pixels, 20)
        controller.record_displacement(20, now=2)
        self.assertIsNone(controller.plan_step(replace(self.conditions(), x=140)))

    def test_sleep_controls_and_work_still_block_goals(self):
        for conditions in (
            replace(self.conditions(), sleeping=True),
            replace(self.conditions(), toolbar_visible=True),
            replace(self.conditions(), observing_computer=True, computer_busy=True),
            replace(self.conditions(), energy=10),
        ):
            controller = WalkController()
            controller.set_goal(200)
            self.assertIsNone(controller.plan_step(conditions))

    def test_cancel_goal_does_not_enable_random_walking(self):
        controller = WalkController()
        controller.set_goal(200)
        controller.set_goal(None)
        self.assertIsNone(controller.plan_step(self.conditions()))
