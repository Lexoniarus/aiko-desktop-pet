"""Canonical room geometry; camera projection never changes these locations."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoomPoint:
    x: float
    depth: float = 1.1

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
        return dict(self.object_depths).get(instance, 1.1)


class RoomGeometry:
    width = 5100.0
    floor_y = 802.0
    # Furniture belongs to the backdrop. The pet and portable objects share a
    # foreground strip whose feet remain visible in the reference's 900px frame.
    foreground_depth = (1.05, 1.13)
    ground_reach = 18.0
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
    def approach(
        cls,
        start: RoomPoint,
        end: RoomPoint,
        seconds: float,
        *,
        speed: float = 310,
    ) -> RoomPoint:
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("Invalid movement interval")
        start, end = cls.accessible(start), cls.accessible(end)
        budget = seconds * speed
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
        back, front = cls.foreground_depth
        return RoomPoint(point.x, max(back, min(front, point.depth)))

    @classmethod
    def route(cls, start: RoomPoint, end: RoomPoint) -> tuple[RoomPoint, ...]:
        """Direct foreground travel, retaining the shortest panorama wrap."""
        return (cls.accessible(end),)
