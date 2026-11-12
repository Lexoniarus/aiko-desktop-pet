"""One transient route executor; WorldState remains the position writer."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..world.room import RoomPoint
from ..world.room_navigation import RoomNavigator


@dataclass(frozen=True, slots=True)
class RoomMotionStep:
    point: RoomPoint
    travelled: tuple[RoomPoint, ...]
    arrived: bool


@dataclass(frozen=True, slots=True)
class PlayerApproach:
    serial: int
    entry: RoomPoint
    target: RoomPoint
    framing: float
    via: RoomPoint | None


class RoomMovement:
    def __init__(self, navigator: RoomNavigator) -> None:
        self.navigator = navigator
        self.goal: RoomPoint | None = None
        self.points: tuple[RoomPoint, ...] = ()
        self.index = 0
        self.serial = 0
        self.travelled: tuple[RoomPoint, ...] = ()

    def player_approach(
        self, start: RoomPoint, wall: str, framing: float,
    ) -> PlayerApproach | None:
        layout = self.navigator.geometry.layout
        across, depth = (
            (layout.width, layout.depth) if wall in ("north", "south")
            else (layout.depth, layout.width)
        )
        stand_off = 180.0
        closest = layout.camera_clearance + layout.pet_radius + 1.0
        if not closest < stand_off <= depth / 2:
            return None
        entry = RoomPoint(
            *layout.wall_to_floor(wall, across / 2, depth / 2 - stand_off),
        )
        stop = stand_off + (closest - stand_off) * framing
        target = RoomPoint(*layout.wall_to_floor(wall, across / 2, depth / 2 - stop))
        if not self.navigator.clear_segment(entry, target):
            return None
        # Aiko may already be on the inward lane. Otherwise route to its far end
        # so the last leg is a genuine straight approach toward the player.
        aligned = (
            start.x == target.x and (target.depth - start.depth) *
            (target.depth - entry.depth) >= 0
        ) if entry.x == target.x else (
            start.depth == target.depth and (target.x - start.x) *
            (target.x - entry.x) >= 0
        )
        via = None if aligned and self.navigator.clear_segment(start, target) else entry
        if via is not None and self.navigator.find_route(start, via) is None:
            return None
        return PlayerApproach(self.serial, entry, target, framing, via)

    def start(
        self, start: RoomPoint, goal: RoomPoint, *, via: RoomPoint | None = None,
    ) -> bool:
        if self.goal == goal and self.index < len(self.points):
            return True
        route = self.navigator.find_route(start, via if via is not None else goal)
        points = route.points[1:] if route else ()
        if route is not None and via is not None:
            if self.navigator.clear_segment(via, goal):
                points = (*points, goal)
            else:
                route = None
                points = ()
        self.serial += 1
        self.goal = goal
        self.points = points
        self.index = 0
        return route is not None

    def advance(self, point: RoomPoint, seconds: float, speed: float) -> RoomMotionStep:
        budget = seconds * speed
        travelled = [point]
        while self.index < len(self.points) and budget > 0:
            target = self.points[self.index]
            distance = self.navigator.geometry.distance(point, target)
            if distance <= budget:
                budget -= distance
                point = target
                self.index += 1
            else:
                fraction = budget / distance
                point = RoomPoint(
                    point.x + (target.x - point.x) * fraction,
                    point.depth + (target.depth - point.depth) * fraction,
                )
                budget = 0
            travelled.append(point)
        self.travelled = tuple(travelled)
        return RoomMotionStep(point, self.travelled, self.index == len(self.points))

    @property
    def next_point(self) -> RoomPoint | None:
        return self.points[self.index] if self.index < len(self.points) else None

    def heading(self, point: RoomPoint, fallback: float) -> float:
        target = self.next_point
        if target is None or target == point:
            return fallback
        return math.atan2(target.x - point.x, point.depth - target.depth)

    def cancel(self) -> None:
        self.goal = None
        self.points = ()
        self.index = 0
        self.travelled = ()
        self.serial += 1
