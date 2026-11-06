"""Room distances and sensory coverage for the shared object coordinators."""

from __future__ import annotations

import math
from dataclasses import replace

from ..infrastructure.world_motion import motion_parameters
from ..pet.mind.object_attention import ObjectAttention
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..world.contracts import ObjectState
from ..world.motion import MotionParameters
from ..world.room import RoomGeometry, RoomPoint
from ..world.state import WorldState


class RoomEnvironment:
    def __init__(self, world: WorldState, geometry: RoomGeometry) -> None:
        self.world, self.geometry = world, geometry
        self.heading = 0.0

    @property
    def position(self) -> RoomPoint:
        room = self.world.snapshot().room
        assert room is not None
        return room.pet

    def object_point(self, instance: str) -> RoomPoint | None:
        item, room = self.world.get(instance), self.world.snapshot().room
        return (RoomPoint(item.position.x, room.depth_for(instance))
                if item.position is not None and room is not None else None)

    def distance_to_place(self, known: ObjectKnowledge) -> float:
        return self.geometry.distance(self.position, RoomPoint(known.x, known.depth))

    def distance_to_object(self, instance: str) -> float:
        point = self.object_point(instance)
        return self.geometry.distance(self.position, point) if point else math.inf

    def _sees(self, point: RoomPoint, height: float, attention: ObjectAttention) -> bool:
        origin = self.position
        dx, dz = point.x - origin.x, point.depth - origin.depth
        distance = math.hypot(dx, dz)
        if attention.mode == "unavailable" or distance > 400:
            return False
        heading = self.heading
        if attention.mode == "survey" and attention.direction is not None:
            side = attention.direction[0]
            if abs(side) >= 0.9:
                heading = math.pi / 2 if side > 0 else -math.pi / 2
        if distance > 100 and dx * math.sin(heading) - dz * math.cos(heading) < 0:
            return False
        for item in self.geometry.layout.furniture:
            if not item.blocking:
                continue
            count = max(2, math.ceil(distance / 6))
            for i in range(1, count):
                fraction = i / count
                ray_height = 65 + (height - 65) * fraction
                if (item.contains(origin.x + dx * fraction, origin.depth + dz * fraction)
                        and item.elevation <= ray_height <= item.elevation + item.height):
                    return False
        return True

    def sees_instance(self, instance: str, attention: ObjectAttention) -> bool:
        item = self.world.get(instance)
        if item.state == ObjectState.PET_HELD:
            return True
        point = self.object_point(instance)
        return bool(point is not None and item.position is not None
                    and self._sees(point, item.position.height, attention))

    def sees_place(self, known: ObjectKnowledge, attention: ObjectAttention) -> bool:
        return self._sees(RoomPoint(known.x, known.depth), known.height, attention)

    def same_place(self, instance: str, known: ObjectKnowledge) -> bool:
        point = self.object_point(instance)
        return point is not None and abs(point.depth - known.depth) < 1

    def approach_target(self, point: RoomPoint) -> RoomPoint:
        return self.geometry.accessible(point)

    @staticmethod
    def motion_parameters() -> MotionParameters:
        native = motion_parameters()
        return replace(native, gravity=native.gravity / 4,
                       minimum_bounce_speed=native.minimum_bounce_speed / 4,
                       settling_speed=native.settling_speed / 4,
                       inward_factor=native.inward_factor / 4)
