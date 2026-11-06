"""Canonical room geometry; camera projection never changes these locations."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .room_layout import RoomLayout


@dataclass(frozen=True, slots=True)
class RoomPoint:
    x: float
    depth: float = 300

    def __post_init__(self) -> None:
        if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0
               for v in (self.x, self.depth)):
            raise ValueError("Invalid room location")

    @property
    def z(self) -> float:
        return self.depth


@dataclass(frozen=True, slots=True)
class RoomAnchor:
    id: str
    name: str
    position: RoomPoint


@dataclass(frozen=True, slots=True)
class RoomSpatialState:
    """World-owned avatar and separate depth, never reinterpret item height."""

    pet: RoomPoint = RoomPoint(400, 100)
    object_depths: tuple[tuple[str, float], ...] = ()
    environment: str = "aiko_room"
    geometry_version: int = 2
    layout_id: str = "aiko-home"
    layout_revision: int = 1

    def __post_init__(self) -> None:
        if self.environment != "aiko_room" or self.geometry_version not in (1, 2):
            raise ValueError("Unknown room environment")
        ids = [key for key, _depth in self.object_depths]
        if len(ids) != len(set(ids)) or len(ids) > 4096:
            raise ValueError("Invalid room object depth inventory")
        for key, depth in self.object_depths:
            if not key or not key.isidentifier():
                raise ValueError("Invalid room object identity")
            RoomPoint(0, depth)

    def depth_for(self, instance: str) -> float:
        return dict(self.object_depths).get(instance, 300)


@dataclass(frozen=True, slots=True)
class RoomGeometry:
    layout: RoomLayout
    ground_reach: float = 12

    @property
    def width(self) -> float:
        return self.layout.width

    @property
    def anchors(self) -> tuple[RoomAnchor, ...]:
        return tuple(
            RoomAnchor(item.id, item.id, RoomPoint(*points[0]))
            for item in self.layout.furniture
            if item.id != "shelf"
            and (points := self.layout.interaction_points(item.id))
        )

    def anchor(self, key: str) -> RoomPoint:
        return next(anchor.position for anchor in self.anchors if anchor.id == key)

    @staticmethod
    def delta(start: float, end: float) -> float:
        return end - start

    @staticmethod
    def distance(start: RoomPoint, end: RoomPoint) -> float:
        return math.hypot(end.x - start.x, end.depth - start.depth)

    def accessible(self, point: RoomPoint, radius: float | None = None) -> RoomPoint:
        """Recover to free ground; ordinary drop validation never calls this."""
        radius = self.layout.pet_radius if radius is None else radius
        if self.layout.can_place(point.x, point.depth, radius):
            return point
        cell = self.layout.cell_size
        candidates = (
            RoomPoint((x + 0.5) * cell, (z + 0.5) * cell)
            for z in range(int(self.layout.depth / cell))
            for x in range(int(self.layout.width / cell))
            if self.layout.can_place((x + 0.5) * cell, (z + 0.5) * cell, radius)
        )
        return min(candidates, key=lambda p: self.distance(p, point))
