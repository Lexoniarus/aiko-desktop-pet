"""Bounded A* over footprint-inflated cells, with continuous checked endpoints."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

from .room import RoomGeometry, RoomPoint


@dataclass(frozen=True, slots=True)
class RoomRoute:
    points: tuple[RoomPoint, ...]


class RoomNavigator:
    def __init__(self, geometry: RoomGeometry) -> None:
        self.geometry = geometry
        layout = geometry.layout
        self.cell = layout.cell_size
        self.grid = Grid(matrix=[
            [int(layout.can_place((x + 0.5) * self.cell, (z + 0.5) * self.cell,
                                  layout.pet_radius))
             for x in range(int(layout.width / self.cell))]
            for z in range(int(layout.depth / self.cell))
        ])
        self.finder = AStarFinder(
            diagonal_movement=DiagonalMovement.only_when_no_obstacle,
        )

    def clear_segment(self, start: RoomPoint, end: RoomPoint) -> bool:
        count = max(1, math.ceil(self.geometry.distance(start, end) / (self.cell / 4)))
        layout = self.geometry.layout
        return all(layout.can_place(
            start.x + (end.x - start.x) * i / count,
            start.depth + (end.depth - start.depth) * i / count,
            layout.pet_radius,
        ) for i in range(count + 1))

    def _node(self, point: RoomPoint) -> tuple[int, int] | None:
        candidates = sorted(
            ((x, z) for z, row in enumerate(self.grid.nodes)
             for x, node in enumerate(row) if node.walkable),
            key=lambda cell: self.geometry.distance(point, self._point(*cell)),
        )
        return next((cell for cell in candidates[:25]
                     if self.clear_segment(point, self._point(*cell))), None)

    def _point(self, x: int, z: int) -> RoomPoint:
        return RoomPoint((x + 0.5) * self.cell, (z + 0.5) * self.cell)

    def find_route(self, start: RoomPoint, goal: RoomPoint) -> RoomRoute | None:
        if self.clear_segment(start, goal):
            return RoomRoute((start, goal))
        first, last = self._node(start), self._node(goal)
        if first is None or last is None:
            return None
        self.grid.cleanup()
        path, _runs = self.finder.find_path(
            self.grid.node(*first), self.grid.node(*last), self.grid,
        )
        if not path:
            return None
        raw = [start, *(self._point(node.x, node.y) for node in path), goal]
        # Remove redundant points only when the whole swept segment stays free.
        points = [raw[0]]
        index = 1
        while index < len(raw):
            end = index
            while end + 1 < len(raw) and self.clear_segment(points[-1], raw[end + 1]):
                end += 1
            if not self.clear_segment(points[-1], raw[end]):
                return None
            points.append(raw[end])
            index = end + 1
        return RoomRoute(tuple(points))

    def nearest_reachable(self, start: RoomPoint, desired: RoomPoint) -> RoomPoint | None:
        target = self.geometry.accessible(desired)
        return target if self.find_route(start, target) is not None else None
