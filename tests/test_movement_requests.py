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

    def test_retarget_preserves_total_distance_time_step_boundaries_and_residual(self):
        self.walk.replace_request("cursor", MotionRequest(
            "cursor", 10, 200, "step", 30, movement_seconds=1,
            step_pixels=8, distance_pixels=16,
        ))
        x = 100.0
        total = 0.0
        for n in range(8):
            if n:
                before = self.walk._progress["cursor"]
                residual = self.walk._residual
                if n == 1:
                    self.assertGreater(residual, 0)
                self.assertTrue(self.walk.retarget("cursor", 10, 220 + n))
                self.assertEqual(self.walk._progress["cursor"], before)
                self.assertEqual(self.walk._residual, residual)
            step = self.walk.plan_step(replace(
                self.conditions, x=x, now=10 + n / 10, elapsed_seconds=.117,
            ))
            if step is None:
                break
            # Native integer displacement leaves a fractional residual.
            moved = int(step.pixels)
            x += moved
            total += moved
            if self.walk.record_displacement(moved, now=10 + n / 10):
                break
        self.assertEqual(total, 16)
        self.assertEqual(self.walk.completion_reason, "budget")
        self.assertFalse(self.walk.retarget("cursor", 10, 500))
        self.walk.release_request("cursor")
        self.walk.replace_request("cursor", MotionRequest("cursor", 10, 500))
        self.assertIsNone(self.walk.request("cursor"))

    def test_reversal_drops_only_signed_residual_and_keeps_consumed_budgets(self):
        self.walk.replace_request("cursor", MotionRequest(
            "cursor", 8, 200, "step", 20, .5, 8, 16,
        ))
        step = self.walk.plan_step(replace(self.conditions, elapsed_seconds=.117))
        assert step is not None
        moved = int(step.pixels)
        self.walk.record_displacement(moved, now=10.1)
        progress = self.walk._progress["cursor"]
        self.assertGreater(self.walk._residual, 0)
        self.assertTrue(self.walk.retarget("cursor", 8, 50))
        self.assertEqual(self.walk._residual, 0)
        self.assertEqual(self.walk._progress["cursor"], progress)
        self.assertEqual(self.walk.remaining_distance, 50 - (100 + moved))
        next_step = self.walk.plan_step(replace(self.conditions, x=100 + moved))
        assert next_step is not None
        self.assertLess(next_step.pixels, 0)
        request = self.walk.request("cursor")
        assert request is not None
        self.assertEqual(request.movement_seconds, .5)
        self.assertEqual(request.distance_pixels, 16)

    def test_same_token_replacement_cannot_extend_deadline_or_budget(self):
        original = MotionRequest("cursor", 3, 150, "step", 20, .5, 8, 16)
        self.walk.replace_request("cursor", original)
        self.walk.plan_step(self.conditions)
        self.walk.record_displacement(4, now=10.1)
        self.walk.replace_request("cursor", replace(
            original, target_x=180, movement_seconds=10,
            distance_pixels=1000, until=100,
        ))
        selected = self.walk.request("cursor")
        self.assertEqual(selected, replace(original, target_x=180))
        self.assertEqual(self.walk._progress["cursor"][2], 4)
        self.walk.set_goal(50)
        self.walk.plan_step(replace(self.conditions, attention_active=False))
        self.assertTrue(self.walk.retarget("cursor", 3, 200))
        self.assertEqual(self.walk.goal_x, 50)
        self.assertEqual(self.walk._progress["cursor"][2], 4)

    def test_attention_does_not_bypass_menu_or_sleep(self):
        self.walk.replace_request("cursor", MotionRequest("cursor", 1, 116, "step", 20))
        self.assertIsNone(
            self.walk.plan_step(replace(self.conditions, menu_engaged=True))
        )
        self.assertIsNone(self.walk.plan_step(replace(self.conditions, sleeping=True)))
