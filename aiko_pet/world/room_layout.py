"""Immutable room dimensions and furniture; independent of rendering and IO."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FurniturePlacement:
    id: str
    asset: str
    x: float
    z: float
    width: float
    depth: float
    height: float
    wall: str | None
    elevation: float
    blocking: bool
    crop: tuple[int, int, int, int]
    pivot: tuple[float, float]

    def contains(self, x: float, z: float, radius: float = 0) -> bool:
        return self.blocking and (
            abs(x - self.x) <= self.width / 2 + radius
            and abs(z - self.z) <= self.depth / 2 + radius
        )


@dataclass(frozen=True, slots=True)
class RoomWall:
    id: str
    asset: str


@dataclass(frozen=True, slots=True)
class RoomLayout:
    id: str
    revision: int
    width: float
    depth: float
    wall_height: float
    cell_size: float
    pet_height: float
    pet_radius: float
    camera_height: float
    camera_clearance: float
    furniture: tuple[FurniturePlacement, ...]
    walls: tuple[RoomWall, ...]
    food_line: float = 0.65

    def wall_to_floor(
        self,
        wall: str,
        along: float,
        distance: float = 0,
    ) -> tuple[float, float]:
        if wall == "north":
            return along, distance
        if wall == "east":
            return self.width - distance, along
        if wall == "south":
            return self.width - along, self.depth - distance
        if wall == "west":
            return distance, self.depth - along
        raise ValueError("Unknown room wall")

    def can_place(self, x: float, z: float, radius: float = 0) -> bool:
        return (
            all(math.isfinite(v) for v in (x, z, radius))
            and radius >= 0
            and radius <= x <= self.width - radius
            and radius <= z <= self.depth - radius
            and math.hypot(x - self.width / 2, z - self.depth / 2)
            >= self.camera_clearance + radius
            and not any(item.contains(x, z, radius) for item in self.furniture)
        )

    def interaction_points(self, key: str) -> tuple[tuple[float, float], ...]:
        item = next(item for item in self.furniture if item.id == key)
        margin = self.pet_radius + self.cell_size
        return tuple(
            (x, z)
            for x, z in (
                (item.x, item.z + item.depth / 2 + margin),
                (item.x, item.z - item.depth / 2 - margin),
                (item.x + item.width / 2 + margin, item.z),
                (item.x - item.width / 2 - margin, item.z),
            )
            if self.can_place(x, z, self.pet_radius)
        )
