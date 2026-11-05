"""Canonical pet motion never depends on Tk, desktop or native taskbar APIs."""

import unittest
from dataclasses import replace

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.pet.movement import WalkConditions
from aiko_pet.pet.movement.random_walk import RandomWalkPlanner


class PetMovementBoundaryTests(unittest.TestCase):
    def test_random_departure_uses_supplied_track_and_energy(self) -> None:
        conditions = WalkConditions(
            now=10, elapsed_seconds=.1, speed_pixels_per_second=50,
            stride_pixels=68, x=0, track=TaskbarTrack(0, 800, 800),
            sprite_width=128, energy=85, auto_walk=True, sleeping=False,
            attention_active=False,
            observing_computer=False, computer_busy=False, quiet_period=False,
            small_idle_steps=True,
        )
        planner = RandomWalkPlanner(next_walk_at=10)
        distance = planner.plan_departure(conditions)
        self.assertIsNotNone(distance)
        assert distance is not None
        self.assertGreater(distance, 0)
        self.assertEqual(planner.next_walk_at, float("inf"))
        self.assertIsNone(planner.plan_departure(replace(conditions, now=11)))
