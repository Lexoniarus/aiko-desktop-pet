"""Canonical room geometry; camera projection never changes these locations."""

from __future__ import annotations

import math
import heapq
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoomPoint:
    x: float
    depth: float = 0.9

    def __post_init__(self) -> None:
        if (
            isinstance(self.x, bool)
            or not math.isfinite(self.x)
            or not 0 <= self.x < 5100
            or isinstance(self.depth, bool)
            or not math.isfinite(self.depth)
            or not 0.2 <= self.depth <= 1.55
        ):
            raise ValueError("Invalid room location")


@dataclass(frozen=True, slots=True)
class RoomAnchor:
    id: str
    name: str
    position: RoomPoint


@dataclass(frozen=True, slots=True)
class RoomSpatialState:
    """World-owned avatar and separate depth, never reinterpret item height."""

    pet: RoomPoint = RoomPoint(600)
    object_depths: tuple[tuple[str, float], ...] = ()
    environment: str = "aiko_room"

    def __post_init__(self) -> None:
        if self.environment != "aiko_room":
            raise ValueError("Unknown room environment")
        ids = [key for key, _depth in self.object_depths]
        if len(ids) != len(set(ids)) or len(ids) > 4096:
            raise ValueError("Invalid room object depth inventory")
        for key, depth in self.object_depths:
            if not key or not key.isidentifier():
                raise ValueError("Invalid room object identity")
            RoomPoint(0, depth)

    def depth_for(self, instance: str) -> float:
        return dict(self.object_depths).get(instance, 0.9)


class RoomGeometry:
    width = 5100.0
    floor_y = 802.0
    # Physical floor footprints, with room for Aiko's feet. Artwork above these
    # footprints may overlap her silhouette without making a whole wall solid.
    obstacles = (
        (680.0, 1180.0, 0.2, 0.43),  # kitchenette
        (1260.0, 1590.0, 0.2, 0.34),  # refrigerator
        (2160.0, 2740.0, 0.59, 1.03),  # freestanding coffee table
        (3615.0, 3885.0, 0.2, 0.38),  # plant
        (4000.0, 4480.0, 0.2, 0.43),  # desk
        (4400.0, 5099.0, 0.2, 0.43),  # bed
    )
    anchors = (
        RoomAnchor("door", "Tür", RoomPoint(315, 0.2)),
        RoomAnchor("kitchen", "Küche", RoomPoint(930, 0.22)),
        RoomAnchor("fridge", "Kühlschrank", RoomPoint(1425, 0.22)),
        RoomAnchor("table", "Tisch", RoomPoint(2450, 1.0)),
        RoomAnchor("desk", "Schreibtisch", RoomPoint(4240, 0.28)),
        RoomAnchor("bed", "Bett", RoomPoint(4780, 0.28)),
    )

    @classmethod
    def delta(cls, start: float, end: float) -> float:
        return (end - start + cls.width / 2) % cls.width - cls.width / 2

    @classmethod
    def distance(cls, start: RoomPoint, end: RoomPoint) -> float:
        return math.hypot(cls.delta(start.x, end.x), (end.depth - start.depth) * 475)

    @classmethod
    def approach(cls, start: RoomPoint, end: RoomPoint, seconds: float) -> RoomPoint:
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid movement interval")
        start, end = cls.accessible(start), cls.accessible(end)
        budget = seconds * 310
        for point in cls.route(start, end):
            distance = cls.distance(start, point)
            fraction = min(1.0, budget / max(0.0001, distance))
            current = RoomPoint(
                (start.x + cls.delta(start.x, point.x) * fraction) % cls.width,
                start.depth + (point.depth - start.depth) * fraction,
            )
            if fraction < 1:
                return current
            budget -= distance
            start = current
        return start

    @classmethod
    def accessible(cls, point: RoomPoint) -> RoomPoint:
        depth = point.depth
        for left, right, back, front in cls.obstacles:
            if left <= point.x <= right and back <= depth <= front:
                depth = front + 0.02
        return RoomPoint(point.x, depth)

    @classmethod
    def route(cls, start: RoomPoint, end: RoomPoint) -> tuple[RoomPoint, ...]:
        """Visibility graph around furniture; camera motion is never an input."""
        source = (start.x, start.depth * 475)
        target = (start.x + cls.delta(start.x, end.x), end.depth * 475)
        rectangles = []
        for left, right, back, front in cls.obstacles:
            center = (left + right) / 2
            offset = start.x + cls.delta(start.x, center) - center
            rectangles.append((left + offset, right + offset, back * 475, front * 475))

        def clear(a: tuple[float, float], b: tuple[float, float]) -> bool:
            for left, right, top, bottom in rectangles:
                low, high = 0.0, 1.0
                for origin, step, minimum, maximum in (
                    (a[0], b[0] - a[0], left + 0.001, right - 0.001),
                    (a[1], b[1] - a[1], top + 0.001, bottom - 0.001),
                ):
                    if abs(step) < 1e-9:
                        if not minimum < origin < maximum:
                            high = -1
                            break
                    else:
                        first, last = sorted((
                            (minimum - origin) / step,
                            (maximum - origin) / step,
                        ))
                        low, high = max(low, first), min(high, last)
                if low < high:
                    return False
            return True

        if clear(source, target):
            return (end,)
        points = [source, target]
        for left, right, top, bottom in rectangles:
            for x in (left - 0.01, right + 0.01):
                for y in (top - 0.01, bottom + 0.01):
                    if 0.2 * 475 <= y <= 1.55 * 475:
                        points.append((x, y))
        distances = {0: 0.0}
        previous: dict[int, int] = {}
        queue = [(0.0, 0)]
        while queue:
            length, index = heapq.heappop(queue)
            if length != distances[index]:
                continue
            if index == 1:
                path = [1]
                while path[-1] != 0:
                    path.append(previous[path[-1]])
                return tuple(
                    RoomPoint(points[i][0] % cls.width, points[i][1] / 475)
                    for i in reversed(path[:-1])
                )
            for other, point in enumerate(points):
                candidate = length + math.dist(points[index], point)
                if candidate < distances.get(other, math.inf) and clear(
                    points[index], point
                ):
                    distances[other] = candidate
                    previous[other] = index
                    heapq.heappush(queue, (candidate, other))
        return (start,)
