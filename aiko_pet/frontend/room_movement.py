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


class RoomMovement:
    def __init__(self, navigator: RoomNavigator) -> None:
        self.navigator = navigator
        self.goal: RoomPoint | None = None
        self.points: tuple[RoomPoint, ...] = ()
        self.index = 0
        self.serial = 0
        self.travelled: tuple[RoomPoint, ...] = ()

    def start(self, start: RoomPoint, goal: RoomPoint) -> bool:
        if self.goal == goal and self.index < len(self.points):
            return True
        route = self.navigator.find_route(start, goal)
        self.serial += 1
        self.goal = goal
        self.points = route.points[1:] if route else ()
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
