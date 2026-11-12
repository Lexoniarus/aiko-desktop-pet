"""Find collision-free room routes on the four walking axes."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from functools import cache

from .room import RoomGeometry, RoomPoint

# Grid indices plus the axis used to enter the point (0 = x, 1 = depth).
_RouteState = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class RoomRoute:
    points: tuple[RoomPoint, ...]


class RoomNavigator:
    def __init__(self, geometry: RoomGeometry) -> None:
        self.geometry = geometry
        layout = geometry.layout
        cell = layout.cell_size
        self._x_lines = tuple((x + 0.5) * cell for x in range(int(layout.width / cell)))
        self._z_lines = tuple((z + 0.5) * cell for z in range(int(layout.depth / cell)))
        self._turn_cost = 2 * cell
        # On a straight segment the closest point to each inflated obstacle
        # lies at an endpoint or at the obstacle center projected onto the axis.
        self._x_probes = (
            layout.width / 2,
            *(item.x for item in layout.furniture if item.blocking),
        )
        self._z_probes = (
            layout.depth / 2,
            *(item.z for item in layout.furniture if item.blocking),
        )

    def clear_segment(self, start: RoomPoint, end: RoomPoint) -> bool:
        layout = self.geometry.layout
        if start.depth == end.depth:
            low, high = sorted((start.x, end.x))
            probes = (low, high, *(x for x in self._x_probes if low < x < high))
            return all(
                layout.can_place(x, start.depth, layout.pet_radius) for x in probes
            )
        if start.x == end.x:
            low, high = sorted((start.depth, end.depth))
            probes = (low, high, *(z for z in self._z_probes if low < z < high))
            return all(layout.can_place(start.x, z, layout.pet_radius) for z in probes)
        return False

    def find_route(self, start: RoomPoint, goal: RoomPoint) -> RoomRoute | None:
        layout = self.geometry.layout
        if not all(
            layout.can_place(point.x, point.depth, layout.pet_radius)
            for point in (start, goal)
        ):
            return None
        if start == goal:
            return RoomRoute((start,))
        if self.clear_segment(start, goal):
            return RoomRoute((start, goal))

        corners = (RoomPoint(goal.x, start.depth), RoomPoint(start.x, goal.depth))
        if abs(start.depth - goal.depth) > abs(start.x - goal.x):
            corners = corners[::-1]
        for corner in corners:
            if (
                corner not in (start, goal)
                and self.clear_segment(start, corner)
                and self.clear_segment(corner, goal)
            ):
                return RoomRoute((start, corner, goal))
        return self._find_detour(start, goal)

    def _find_detour(self, start: RoomPoint, goal: RoomPoint) -> RoomRoute | None:
        # Include both endpoint coordinates so the route reaches them exactly
        # and does not need short corrective steps to/from nearby cell centers.
        xs = sorted({*self._x_lines, start.x, goal.x})
        zs = sorted({*self._z_lines, start.depth, goal.depth})
        origin = (xs.index(start.x), zs.index(start.depth), -1)
        target = (xs.index(goal.x), zs.index(goal.depth))

        @cache
        def point(x: int, z: int) -> RoomPoint:
            return RoomPoint(xs[x], zs[z])

        @cache
        def clear(a: tuple[int, int], b: tuple[int, int]) -> bool:
            return self.clear_segment(point(*a), point(*b))

        def remaining(x: int, z: int) -> float:
            return abs(xs[x] - goal.x) + abs(zs[z] - goal.depth)

        queue: list[tuple[float, int, float, _RouteState]] = [
            (remaining(*origin[:2]), 0, 0.0, origin)
        ]
        costs: dict[_RouteState, tuple[float, int]] = {origin: (0.0, 0)}
        previous: dict[_RouteState, _RouteState] = {}
        while queue:
            _, bends, cost, state = heapq.heappop(queue)
            if (cost, bends) != costs[state]:
                continue
            x, z, axis = state
            if (x, z) == target:
                points = [goal]
                while state != origin:
                    parent = previous[state]
                    if parent[2] != state[2]:
                        points.append(point(*parent[:2]))
                    state = parent
                return RoomRoute(tuple(reversed(points)))

            for dx, dz, direction in ((1, 0, 0), (-1, 0, 0), (0, 1, 1), (0, -1, 1)):
                nx, nz = x + dx, z + dz
                if not (0 <= nx < len(xs) and 0 <= nz < len(zs)):
                    continue
                a, b = sorted(((x, z), (nx, nz)))
                if not clear(a, b):
                    continue
                turn = axis != -1 and axis != direction
                distance = abs(xs[nx] - xs[x]) + abs(zs[nz] - zs[z])
                new_cost = cost + distance + self._turn_cost * turn
                new_bends = bends + turn
                neighbor = (nx, nz, direction)
                if (new_cost, new_bends) >= costs.get(neighbor, (float("inf"), 0)):
                    continue
                costs[neighbor] = (new_cost, new_bends)
                previous[neighbor] = state
                heapq.heappush(
                    queue, (new_cost + remaining(nx, nz), new_bends, new_cost, neighbor)
                )
        return None

    def nearest_reachable(
        self, start: RoomPoint, desired: RoomPoint
    ) -> RoomPoint | None:
        target = self.geometry.accessible(desired)
        return target if self.find_route(start, target) is not None else None
