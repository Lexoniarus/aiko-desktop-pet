"""Canonical pet motion never depends on Tk, desktop or native taskbar APIs."""

import ast
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.pet.movement import WalkConditions, WalkController
from aiko_pet.pet.movement.random_walk import RandomWalkPlanner


class PetMovementBoundaryTests(unittest.TestCase):
    def test_canonical_controller_has_one_pet_owner(self) -> None:
        self.assertEqual(WalkController.__module__, "aiko_pet.pet.movement.controller")

    def test_domain_movement_has_no_native_adapter_imports(self) -> None:
        source = Path(__file__).resolve().parents[1] / "aiko_pet" / "pet" / "movement"
        for path in source.glob("*.py"):
            with self.subTest(path=path.name):
                module = ast.parse(path.read_text("utf-8"))
                imports = [
                    node.module or "" for node in ast.walk(module)
                    if isinstance(node, ast.ImportFrom)
                ]
                self.assertFalse(any(
                    "desktop" in name or "tkinter" in name
                    for name in imports
                ))

    def test_random_departure_uses_supplied_track_and_energy(self) -> None:
        conditions = WalkConditions(
            now=10, elapsed_seconds=.1, speed_pixels_per_second=50,
            stride_pixels=68, x=0, track=TaskbarTrack(0, 800, 800),
            sprite_width=128, energy=85, auto_walk=True, sleeping=False,
            attention_active=False, menu_engaged=False,
            observing_computer=False, computer_busy=False, quiet_period=False,
        )
        planner = RandomWalkPlanner(next_walk_at=10)
        distance = planner.plan_departure(conditions)
        self.assertIsNotNone(distance)
        assert distance is not None
        self.assertGreater(distance, 0)
        self.assertEqual(planner.next_walk_at, float("inf"))
        self.assertIsNone(planner.plan_departure(replace(conditions, now=11)))
