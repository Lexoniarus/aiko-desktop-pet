"""Plan routes along radial lines and constant-distance arcs around the player."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from functools import cache

from .room import RoomGeometry, RoomPoint, bearing_delta

_EPSILON = 1e-8
_RouteState = tuple[int, int, int]
_Box = tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class RoomLeg:
    geometry: RoomGeometry
    start: RoomPoint
    end: RoomPoint
    bearing: float
    radius: float
    turn: float
    radial_change: float

    @classmethod
    def between(
        cls,
        geometry: RoomGeometry,
        start: RoomPoint,
        end: RoomPoint,
    ) -> RoomLeg | None:
        bearing, radius = geometry.polar(start)
        end_bearing, end_radius = geometry.polar(end)
        turn = bearing_delta(bearing, end_bearing)
        radial_change = end_radius - radius
        if abs(turn) <= _EPSILON:
            return cls(geometry, start, end, bearing, radius, 0.0, radial_change)
        if abs(radial_change) <= _EPSILON:
            return cls(geometry, start, end, bearing, radius, turn, 0.0)
        return None

    @property
    def length(self) -> float:
        return abs(self.radius * self.turn) if self.turn else abs(self.radial_change)

    @property
    def side(self) -> int:
        return (self.turn > 0) - (self.turn < 0)

    def point(self, fraction: float) -> RoomPoint:
        if fraction <= 0:
            return self.start
        if fraction >= 1:
            return self.end
        return RoomPoint(
            *self.geometry.polar_position(
                self.bearing + self.turn * fraction,
                self.radius + self.radial_change * fraction,
            )
        )

    def heading(self, fraction: float = 0) -> float:
        if self.turn:
            return self.bearing + self.turn * fraction + self.side * math.pi / 2
        return self.bearing + (math.pi if self.radial_change < 0 else 0)

    def covers_angle(self, bearing: float) -> bool:
        signed_turn = ((bearing - self.bearing) * self.side) % math.tau
        return (
            signed_turn <= abs(self.turn) + _EPSILON
            or signed_turn >= math.tau - _EPSILON
        )


@dataclass(frozen=True, slots=True)
class RoomRoute:
    points: tuple[RoomPoint, ...]


def _ray_hits_box(start: RoomPoint, end: RoomPoint, box: _Box) -> bool:
    entry, exit_ = 0.0, 1.0
    for origin, target, low, high in (
        (start.x, end.x, box[0], box[1]),
        (start.depth, end.depth, box[2], box[3]),
    ):
        delta = target - origin
        if abs(delta) <= _EPSILON:
            if not low <= origin <= high:
                return False
            continue
        first, last = sorted(((low - origin) / delta, (high - origin) / delta))
        entry, exit_ = max(entry, first), min(exit_, last)
        if entry > exit_ + _EPSILON:
            return False
    return True


class RoomNavigator:
    def __init__(self, geometry: RoomGeometry) -> None:
        self.geometry = geometry
        layout = geometry.layout
        cell = layout.cell_size
        self._min_radius = layout.camera_clearance + layout.pet_radius
        angle_count = math.ceil(math.tau * geometry.outer_distance / cell)
        self._angles = tuple(
            math.tau * index / angle_count for index in range(angle_count)
        )
        self._radii = tuple(
            self._min_radius + _EPSILON + index * cell
            for index in range(
                math.ceil((geometry.outer_distance - self._min_radius) / cell)
            )
        )
        margin = layout.pet_radius + _EPSILON
        self._boxes: tuple[_Box, ...] = tuple(
            (
                item.x - item.width / 2 - margin,
                item.x + item.width / 2 + margin,
                item.z - item.depth / 2 - margin,
                item.z + item.depth / 2 + margin,
            )
            for item in layout.furniture
            if item.blocking
        )

    def _arc_hits_box(self, leg: RoomLeg, box: _Box) -> bool:
        cx = self.geometry.layout.width / 2
        cz = self.geometry.layout.depth / 2
        x0, x1, z0, z1 = box
        for x in (x0, x1):
            square = leg.radius**2 - (x - cx) ** 2
            if square >= 0:
                root = math.sqrt(square)
                for z in (cz - root, cz + root):
                    if z0 <= z <= z1 and leg.covers_angle(math.atan2(x - cx, cz - z)):
                        return True
        for z in (z0, z1):
            square = leg.radius**2 - (z - cz) ** 2
            if square >= 0:
                root = math.sqrt(square)
                for x in (cx - root, cx + root):
                    if x0 <= x <= x1 and leg.covers_angle(math.atan2(x - cx, cz - z)):
                        return True
        return False

    def clear_segment(self, start: RoomPoint, end: RoomPoint) -> bool:
        layout = self.geometry.layout
        if not all(
            layout.can_place(point.x, point.depth, layout.pet_radius)
            for point in (start, end)
        ):
            return False
        leg = RoomLeg.between(self.geometry, start, end)
        if leg is None:
            return False
        if not leg.turn:
            return not any(_ray_hits_box(start, end, box) for box in self._boxes)
        # The extrema bound the arc against room walls. Intersections with each
        # inflated furniture box catch obstructions between valid endpoints.
        for angle in (0, math.pi / 2, math.pi, -math.pi / 2):
            if leg.covers_angle(angle) and not layout.can_place(
                *self.geometry.polar_position(angle, leg.radius),
                layout.pet_radius,
            ):
                return False
        return not any(self._arc_hits_box(leg, box) for box in self._boxes)

    def _point(self, angle: float, radius: float) -> RoomPoint | None:
        x, z = self.geometry.polar_position(angle, radius)
        layout = self.geometry.layout
        margin = layout.pet_radius
        if (
            margin <= x <= layout.width - margin
            and margin <= z <= layout.depth - margin
        ):
            return RoomPoint(x, z)
        return None

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

        start_angle, start_radius = self.geometry.polar(start)
        goal_angle, goal_radius = self.geometry.polar(goal)
        corners = (
            self._point(goal_angle, start_radius),
            self._point(start_angle, goal_radius),
        )
        options: list[tuple[float, RoomPoint]] = []
        for corner in corners:
            if (
                corner is not None
                and corner not in (start, goal)
                and self.clear_segment(start, corner)
                and self.clear_segment(corner, goal)
            ):
                # Prefer the shorter route if both one-turn paths are open.
                length = abs(bearing_delta(start_angle, goal_angle)) * (
                    self.geometry.polar(corner)[1]
                ) + abs(start_radius - goal_radius)
                options.append((length, corner))
        if options:
            _, corner = min(options, key=lambda option: option[0])
            return RoomRoute((start, corner, goal))
        return self._find_detour(start, goal)

    def _find_detour(self, start: RoomPoint, goal: RoomPoint) -> RoomRoute | None:
        start_angle, start_radius = self.geometry.polar(start)
        goal_angle, goal_radius = self.geometry.polar(goal)
        start_angle %= math.tau
        goal_angle %= math.tau
        angles = sorted({*self._angles, start_angle, goal_angle})
        radii = sorted({
            *(
                radius
                for radius in self._radii
                if min(abs(radius - start_radius), abs(radius - goal_radius)) > _EPSILON
            ),
            start_radius,
            goal_radius,
        })
        origin = (angles.index(start_angle), radii.index(start_radius), -1)
        target = (angles.index(goal_angle), radii.index(goal_radius))

        @cache
        def point(a: int, r: int) -> RoomPoint | None:
            if (a, r) == origin[:2]:
                return start
            if (a, r) == target:
                return goal
            return self._point(angles[a], radii[r])

        @cache
        def clear(a: tuple[int, int], b: tuple[int, int]) -> bool:
            first, second = point(*a), point(*b)
            return (
                first is not None
                and second is not None
                and self.clear_segment(first, second)
            )

        def remaining(a: int, r: int) -> float:
            turn = abs(bearing_delta(angles[a], goal_angle))
            radius = radii[r]
            # Without obstacles, travelling inwards saves arc length only
            # after the angle exceeds the cost of the inward/outward pair.
            inner = min(radius, goal_radius) if turn <= 2 else self._min_radius
            return radius + goal_radius - 2 * inner + turn * inner

        queue: list[tuple[float, float, _RouteState]] = [
            (remaining(*origin[:2]), 0.0, origin),
        ]
        costs: dict[_RouteState, float] = {origin: 0.0}
        previous: dict[_RouteState, _RouteState] = {}
        while queue:
            _, cost, state = heapq.heappop(queue)
            if cost != costs[state]:
                continue
            a, r, axis = state
            if (a, r) == target:
                steps = [goal]
                while state != origin:
                    state = previous[state]
                    previous_point = point(*state[:2])
                    assert previous_point is not None
                    if len(steps) > 1 and self.clear_segment(previous_point, steps[-2]):
                        steps.pop()
                    steps.append(previous_point)
                return RoomRoute(tuple(reversed(steps)))

            for na, nr, direction in (
                ((a + 1) % len(angles), r, 0),
                ((a - 1) % len(angles), r, 0),
                (a, r + 1, 1),
                (a, r - 1, 1),
            ):
                if not 0 <= nr < len(radii):
                    continue
                first, second = sorted(((a, r), (na, nr)))
                if not clear(first, second):
                    continue
                distance = (
                    abs(bearing_delta(angles[a], angles[na])) * radii[r]
                    if direction == 0
                    else abs(radii[nr] - radii[r])
                )
                turn = axis != -1 and axis != direction
                new_cost = cost + distance + 2 * self.geometry.layout.cell_size * turn
                neighbor = (na, nr, direction)
                if new_cost >= costs.get(neighbor, math.inf):
                    continue
                costs[neighbor] = new_cost
                previous[neighbor] = state
                heapq.heappush(
                    queue, (new_cost + remaining(na, nr), new_cost, neighbor)
                )
        return None
