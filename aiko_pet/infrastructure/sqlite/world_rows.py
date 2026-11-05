"""Map paired stock/knowledge using existing safe restore and strict codecs.

World truth never supplies subjective identity. Remembered physical references
are historical facts, not foreign keys requiring an object still in stock.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from typing import Any

from ...pet.mind.object_knowledge import ObjectMemorySnapshot
from ...pet.mind.object_perception import ConsumableKind
from ...world.contracts import (
    ObjectDefinition,
    ObjectInteraction,
    WorldSnapshot,
    WorldSurface,
)
from ..object_memory_codec import decode_object_memory, encode_object_memory
from ..world_codec import decode_world, encode_world
from .rows import boolean, read_rows, require_transaction, upsert_singleton


def _identities(definitions: tuple[ObjectDefinition, ...]) -> dict[str, ConsumableKind]:
    return {
        item.food_id or item.definition_id: "book"
        if ObjectInteraction.READ in item.interactions
        else "drink"
        if ObjectInteraction.DRINK in item.interactions
        else "food"
        for item in definitions
    }


def _write_memory(
    connection: sqlite3.Connection,
    raw: dict[str, Any],
) -> None:
    upsert_singleton(
        connection,
        "object_memory_state",
        {
            "next_record_id": raw["next_record_id"],
            "world_next_id": raw["world_next_id"],
        },
    )
    for index, item in enumerate(raw["entries"]):
        connection.execute(
            "INSERT INTO object_memories VALUES "
            "(?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item["token"],
                index,
                item["identity"],
                item["kind"],
                item["x"],
                item["height"],
                int(item["resting"]),
                item["age_seconds"],
                int(item["assessed"]),
                item["disposition"],
                item["place_status"],
                item["instance_id"],
            ),
        )
    connection.executemany(
        "INSERT INTO object_memory_sources VALUES (?, ?, ?)",
        [
            (item["token"], source, index)
            for item in raw["entries"]
            for index, source in enumerate(item["possible_sources"])
        ],
    )


def write_world_memory(
    connection: sqlite3.Connection,
    world: WorldSnapshot | None,
    memory: ObjectMemorySnapshot | None,
    *,
    recovery_x: float,
) -> None:
    require_transaction(connection)
    if memory is not None and world is None:
        raise ValueError("Object memory requires its paired World snapshot")
    raw_world = None if world is None else encode_world(world, recovery_x=recovery_x)
    raw_memory = None
    if world is not None:
        decode_world(raw_world, world.definitions)
        if memory is not None:
            raw_memory = encode_object_memory(
                memory,
                world_next_id=world.next_instance_id,
            )
            decode_object_memory(
                raw_memory,
                _identities(world.definitions),
                allocated_until=world.next_instance_id,
            )
    # Validate before replacing owned rows, and never commit the caller's snapshot.
    connection.execute("DELETE FROM object_memory_state")
    connection.execute("DELETE FROM world_objects")
    if world is None:
        connection.execute("DELETE FROM world_state")
        return
    assert raw_world is not None
    upsert_singleton(
        connection,
        "world_state",
        {
            "width": world.surface.width,
            "height": world.surface.height,
            "ground_inset": world.surface.ground_inset,
            "revision": world.revision,
            "next_instance_id": world.next_instance_id,
        },
    )
    connection.executemany(
        "INSERT INTO world_objects VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["id"],
                index,
                row["definition_id"],
                row["revision"],
                row["x"],
                *row["footprint"],
                row.get("expires_at"),
            )
            for index, row in enumerate(raw_world["objects"])
        ],
    )
    if raw_memory is not None:
        _write_memory(connection, raw_memory)


def _read_memory(
    connection: sqlite3.Connection,
    world: WorldSnapshot,
) -> ObjectMemorySnapshot | None:
    states = read_rows(connection, "SELECT * FROM object_memory_state WHERE id = 1")
    if not states:
        return None
    state = states[0]
    sources: dict[str, list[str]] = {}
    for source in read_rows(
        connection, "SELECT * FROM object_memory_sources ORDER BY token, position_index"
    ):
        sources.setdefault(source["token"], []).append(source["source_token"])
    raw: dict[str, Any] = dict(
        version=3,
        next_record_id=state["next_record_id"],
        world_next_id=state["world_next_id"],
        entries=[],
    )
    for item in read_rows(
        connection, "SELECT * FROM object_memories ORDER BY position_index"
    ):
        del item["memory_id"], item["position_index"]
        item["resting"] = boolean(item["resting"])
        item["assessed"] = boolean(item["assessed"])
        item["possible_sources"] = sources.get(item["token"], [])
        raw["entries"].append(item)
    return decode_object_memory(
        raw, _identities(world.definitions), allocated_until=world.next_instance_id
    )


def read_world_memory(
    connection: sqlite3.Connection,
    definitions: tuple[ObjectDefinition, ...],
) -> tuple[WorldSnapshot | None, ObjectMemorySnapshot | None]:
    states = read_rows(connection, "SELECT * FROM world_state WHERE id = 1")
    if not states:
        return None, None
    state = states[0]
    objects = read_rows(
        connection, "SELECT * FROM world_objects ORDER BY position_index"
    )
    raw = dict(
        version=2,
        surface=[state["width"], state["height"]],
        revision=state["revision"],
        next_instance_id=state["next_instance_id"],
        objects=[
            dict(
                id=item["instance_id"],
                definition_id=item["definition_id"],
                revision=item["revision"],
                x=item["x"],
                footprint=[item["footprint_left"], item["footprint_right"]],
                expires_at=item["expires_at"],
            )
            for item in objects
        ],
    )
    surface = WorldSurface(state["width"], state["height"], state["ground_inset"])
    world = replace(decode_world(raw, definitions), surface=surface)
    if any(
        item.position is None
        or item.position.x
        != surface.ground_x(
            item.position.x,
            item.footprint,
        )
        for item in world.objects
    ):
        raise ValueError("Saved stock is outside reachable ground")
    return world, _read_memory(connection, world)
