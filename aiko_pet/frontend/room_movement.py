"""One transient route executor; WorldState remains the position writer."""

from __future__ import annotations

from dataclasses import dataclass

from ..world.room import RoomPoint
from ..world.room_navigation import RoomLeg, RoomNavigator


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
        self._legs: tuple[RoomLeg, ...] = ()
        self.index = 0
        self._leg_progress = 0.0
        self.distance_walked = 0.0
        self.serial = 0
        self.travelled: tuple[RoomPoint, ...] = ()

    def start(self, start: RoomPoint, goal: RoomPoint) -> bool:
        if self.goal == goal and self.index < len(self.points):
            return True
        route = self.navigator.find_route(start, goal)
        legs: list[RoomLeg] = []
        if route is not None:
            for first, second in zip(route.points, route.points[1:]):
                leg = RoomLeg.between(self.navigator.geometry, first, second)
                assert leg is not None
                if leg.length:
                    legs.append(leg)
        self.serial += 1
        self.goal = goal
        self._legs = tuple(legs)
        self.points = tuple(leg.end for leg in legs)
        self.index = 0
        self._leg_progress = 0.0
        return route is not None

    def advance(self, point: RoomPoint, seconds: float, speed: float) -> RoomMotionStep:
        budget = seconds * speed
        travelled = [point]
        while (leg := self.leg) is not None and budget > 0:
            remaining = leg.length - self._leg_progress
            travelled_now = min(remaining, budget)
            self._leg_progress += travelled_now
            self.distance_walked += travelled_now
            budget -= travelled_now
            if travelled_now == remaining:
                point = leg.end
                self.index += 1
                self._leg_progress = 0.0
            else:
                point = leg.point(self._leg_progress / leg.length)
            travelled.append(point)
        self.travelled = tuple(travelled)
        return RoomMotionStep(point, self.travelled, self.index == len(self.points))

    @property
    def leg(self) -> RoomLeg | None:
        return self._legs[self.index] if self.index < len(self._legs) else None

    def heading(self, fallback: float) -> float:
        leg = self.leg
        return leg.heading(self._leg_progress / leg.length) if leg else fallback

    def cancel(self) -> None:
        self.goal = None
        self.points = ()
        self._legs = ()
        self.index = 0
        self._leg_progress = 0.0
        self.travelled = ()
        self.serial += 1
