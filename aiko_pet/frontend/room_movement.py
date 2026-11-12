"""One transient route executor; WorldState remains the position writer."""

from __future__ import annotations

from dataclasses import dataclass

from ..world.room import RoomPoint
from ..world.room_navigation import RoomLeg, RoomNavigator, RoomRoute

CALL_DISTANCE = 70.0
_DISTANCE_TOLERANCE = 1e-8


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
        route = self.plan(start, goal)
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

    @property
    def _room_clearance(self) -> float:
        layout = self.navigator.geometry.layout
        return layout.camera_clearance + layout.pet_radius

    def _transition(self, bearing: float) -> RoomPoint:
        return RoomPoint(
            *self.navigator.geometry.polar_position(bearing, self._room_clearance + 1)
        )

    def _call_ray_is_clear(self, start: RoomPoint, goal: RoomPoint) -> bool:
        return self.navigator.clear_segment(
            start, goal, minimum_distance=CALL_DISTANCE - _DISTANCE_TOLERANCE,
        )

    def call_target(self, bearing: float) -> RoomPoint:
        geometry = self.navigator.geometry
        transition = self._transition(bearing)
        near = RoomPoint(*geometry.polar_position(bearing, CALL_DISTANCE))
        if self._call_ray_is_clear(transition, near):
            return near
        return geometry.accessible(transition)

    def recover_position(self, point: RoomPoint) -> RoomPoint:
        geometry = self.navigator.geometry
        bearing, distance = geometry.polar(point)
        if (
            distance < self._room_clearance
            and self._call_ray_is_clear(point, self._transition(bearing))
        ):
            return point
        return geometry.accessible(point)

    def plan(self, start: RoomPoint, goal: RoomPoint) -> RoomRoute | None:
        geometry = self.navigator.geometry
        start_bearing, start_distance = geometry.polar(start)
        goal_bearing, goal_distance = geometry.polar(goal)
        starts_close = start_distance < self._room_clearance
        ends_close = goal_distance < self._room_clearance
        if starts_close and ends_close and self._call_ray_is_clear(start, goal):
            return RoomRoute((start, goal))

        # Route on the ordinary floor between the two optional radial legs.
        entry = self._transition(start_bearing) if starts_close else start
        exit_ = self._transition(goal_bearing) if ends_close else goal
        if starts_close and not self._call_ray_is_clear(start, entry):
            return None
        if ends_close and not self._call_ray_is_clear(exit_, goal):
            return None
        route = self.navigator.find_route(entry, exit_)
        if route is None:
            return None
        return RoomRoute((
            *((start,) if starts_close else ()),
            *route.points,
            *((goal,) if ends_close else ()),
        ))

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
