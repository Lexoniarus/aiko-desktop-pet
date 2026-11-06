"""Transform legacy panorama places without learning objective stock locations."""

from __future__ import annotations

import math
from dataclasses import replace

from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..world.contracts import (
    ObjectFootprint,
    WorldPosition,
    WorldSnapshot,
    WorldSurface,
)
from ..world.room import RoomGeometry, RoomPoint, RoomSpatialState
from .room_layout import load_room_layout


def legacy_point(x: float, depth: float) -> RoomPoint:
    angle = (x % 5100) / 5100 * math.tau - math.pi / 2
    dx, dz = math.cos(angle), math.sin(angle)
    inset = 45 + max(0, min(1, (depth - 0.2) / 1.35)) * 95
    distance = min(
        (400 - inset) / max(abs(dx), 1e-9), (300 - inset) / max(abs(dz), 1e-9)
    )
    return RoomPoint(400 + dx * distance, 300 + dz * distance)


def migrate_legacy_room(
    world: WorldSnapshot,
    memory: ObjectMemorySnapshot | None,
) -> tuple[WorldSnapshot, ObjectMemorySnapshot | None]:
    room = world.room
    if room is None or room.geometry_version == 2:
        return world, memory
    geometry = RoomGeometry(load_room_layout())
    objects = []
    depths = []
    for item in world.objects:
        position = item.position
        if position is not None:
            point = geometry.accessible(
                legacy_point(position.x, room.depth_for(item.instance_id)),
                radius=8,
            )
            item = replace(
                item,
                position=WorldPosition(point.x, position.height / 4),
                footprint=ObjectFootprint(
                    item.footprint.left / 4,
                    item.footprint.right / 4,
                ),
            )
            depths.append((item.instance_id, point.depth))
        objects.append(item)
    if memory is not None:
        memory = replace(
            memory,
            entries=tuple(
                replace(
                    entry,
                    x=(p := legacy_point(entry.x, entry.depth)).x,
                    depth=p.depth,
                    height=entry.height / 4,
                )
                for entry in memory.entries
            ),
        )
    spatial = RoomSpatialState(
        geometry.accessible(legacy_point(room.pet.x, room.pet.depth)),
        tuple(depths),
    )
    return replace(
        world, surface=WorldSurface(800, 225, 6), objects=tuple(objects), room=spatial
    ), memory
