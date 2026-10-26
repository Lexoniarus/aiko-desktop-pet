"""Source releases and stable IDs share exactly one motion controller."""

import unittest
from dataclasses import replace

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.pet.movement.contracts import MotionRequest, WalkConditions
from aiko_pet.pet.movement.controller import WalkController


class MovementRequestTests(unittest.TestCase):
    def setUp(self):
        self.walk = WalkController(next_walk_at=999)
        self.conditions = WalkConditions(
            now=10,
            elapsed_seconds=0.1,
            speed_pixels_per_second=40,
            stride_pixels=68,
            x=100,
            track=TaskbarTrack(0, 800, 600),
            sprite_width=192,
            energy=80,
            auto_walk=True,
            sleeping=False,
            attention_active=True,
            menu_engaged=False,
            observing_computer=False,
            computer_busy=False,
            quiet_period=False,
        )

    def test_world_hold_does_not_erase_cursor_request(self):
        request = MotionRequest("cursor", 1, 116, "step", 20)
        self.walk.replace_request("cursor", request)
        self.walk.set_goal(None)
        step = self.walk.plan_step(self.conditions)
        self.assertIsNotNone(step)
        self.assertEqual(self.walk.source, "cursor")
        self.walk.replace_request("cursor", request)
        self.assertEqual(self.walk.remaining_distance, 16)

    def test_world_takes_priority_and_source_release_is_specific(self):
        self.walk.replace_request("cursor", MotionRequest("cursor", 1, 116, "step", 20))
        self.walk.set_goal(80)
        step = self.walk.plan_step(replace(self.conditions, attention_active=False))
        assert step is not None
        self.assertEqual(step.direction, -1)
        self.walk.release_request("cursor")
        self.assertEqual(self.walk.goal_x, 80)

    def test_completed_and_expired_requests_do_not_restart(self):
        self.walk.replace_request("cursor", MotionRequest("cursor", 1, 104, "step", 20))
        self.walk.plan_step(self.conditions)
        self.walk.record_displacement(4, now=10.1)
        self.assertIsNone(
            self.walk.plan_step(replace(self.conditions, x=104, now=10.2))
        )
        self.walk.replace_request("cursor", MotionRequest("cursor", 2, 116, "step", 9))
        self.assertIsNone(self.walk.plan_step(self.conditions))

    def test_attention_does_not_bypass_menu_or_sleep(self):
        self.walk.replace_request("cursor", MotionRequest("cursor", 1, 116, "step", 20))
        self.assertIsNone(
            self.walk.plan_step(replace(self.conditions, menu_engaged=True))
        )
        self.assertIsNone(self.walk.plan_step(replace(self.conditions, sleeping=True)))
