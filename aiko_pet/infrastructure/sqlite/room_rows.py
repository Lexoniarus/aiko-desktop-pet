"""Map optional room geometry within the existing complete save transaction."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import replace

from ...world.contracts import ObjectState, WorldSnapshot
from ...world.room import RoomPoint, RoomSpatialState
from .rows import require_transaction

ROOM_SCHEMA = (
    """CREATE TABLE room_state (
    id INTEGER PRIMARY KEY REFERENCES world_state(id) ON DELETE CASCADE CHECK(id=1),
    environment TEXT NOT NULL CHECK(environment='aiko_room'),
    pet_x REAL NOT NULL CHECK(pet_x >= 0 AND pet_x < 5100),
    pet_depth REAL NOT NULL CHECK(pet_depth >= 0.2 AND pet_depth <= 1.55),
    object_depths TEXT NOT NULL
)""",
)


def write_room(connection: sqlite3.Connection, world: WorldSnapshot | None) -> None:
    require_transaction(connection)
    connection.execute("DELETE FROM room_state")
    if world is None or world.room is None:
        return
    room = world.room
    ids = {item.instance_id for item in world.objects}
    if any(key not in ids for key, _depth in room.object_depths):
        raise ValueError("Room object is outside its World")
    retained = {
        item.instance_id
        for item in world.objects
        if item.state not in (ObjectState.CONSUMED, ObjectState.REMOVED)
    }
    connection.execute(
        "INSERT INTO room_state VALUES (1, ?, ?, ?, ?, ?, ?, ?)",
        (
            room.environment,
            room.pet.x,
            room.pet.depth,
            json.dumps([
                (key, depth) for key, depth in room.object_depths if key in retained
            ]),
            room.geometry_version,
            room.layout_id,
            room.layout_revision,
        ),
    )


def read_room(connection: sqlite3.Connection, world: WorldSnapshot) -> WorldSnapshot:
    row = connection.execute("SELECT * FROM room_state WHERE id=1").fetchone()
    if row is None:
        return world
    raw = json.loads(row[4])
    if not isinstance(raw, list) or any(
        not isinstance(entry, list) or len(entry) != 2 for entry in raw
    ):
        raise ValueError("Invalid saved room depths")
    room = RoomSpatialState(
        RoomPoint(row[2], row[3]),
        tuple((entry[0], entry[1]) for entry in raw),
        row[1],
        row[5],
        row[6],
        row[7],
    )
    ids = {item.instance_id for item in world.objects}
    if any(key not in ids for key, _depth in room.object_depths):
        raise ValueError("Saved room depth references absent stock")
    return replace(world, room=room)
