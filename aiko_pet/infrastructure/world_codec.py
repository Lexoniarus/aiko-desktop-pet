"""Versioned durable World values; restore transient objects safely on ground."""

from __future__ import annotations

import math
import re
from typing import Any

from ..pet.catalog_validation import object_fields
from ..world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldObjectSnapshot,
    WorldPosition,
    WorldSnapshot,
    WorldSurface,
)


def encode_world(snapshot: WorldSnapshot, *, recovery_x: float) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for item in snapshot.objects:
        if item.state in (ObjectState.CONSUMED, ObjectState.REMOVED):
            continue
        x = item.position.x if item.position is not None else recovery_x
        x = snapshot.surface.ground_x(x, item.footprint)
        records.append({
            "id": item.instance_id,
            "definition_id": item.definition_id,
            "revision": item.revision + int(item.state != ObjectState.RESTING),
            "x": x,
            "footprint": [item.footprint.left, item.footprint.right],
            "expires_at": item.expires_at,
        })
    return {
        "version": 2,
        "surface": [snapshot.surface.width, snapshot.surface.height],
        "revision": snapshot.revision,
        "next_instance_id": snapshot.next_instance_id,
        "objects": records,
    }


def _number(raw: Any) -> float:
    if type(raw) not in (int, float) or not math.isfinite(raw) or raw < 0:
        raise ValueError("Invalid World numeric value")
    return float(raw)


def _pair(raw: Any) -> tuple[float, float]:
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("World geometry requires two numbers")
    return _number(raw[0]), _number(raw[1])


def _integer(raw: Any) -> int:
    if type(raw) is not int or raw < 0:
        raise ValueError("World revision/counter requires an integer")
    return int(raw)


def decode_world(
    raw: Any,
    definitions: tuple[ObjectDefinition, ...],
) -> WorldSnapshot:
    data = object_fields(
        raw,
        (
            "version",
            "surface",
            "revision",
            "next_instance_id",
            "objects",
        ),
        context="saved World",
    )
    if type(data["version"]) is not int or data["version"] not in (1, 2):
        raise ValueError("Unsupported World save version")
    surface = WorldSurface(*_pair(data["surface"]))
    revision, next_id = _integer(data["revision"]), _integer(data["next_instance_id"])
    definitions_by_id = {item.definition_id: item for item in definitions}
    objects: list[WorldObjectSnapshot] = []
    ids: set[str] = set()
    if not isinstance(data["objects"], list):
        raise ValueError("World objects must be a list")
    for entry in data["objects"]:
        row = object_fields(
            entry,
            (
                "id",
                "definition_id",
                "revision",
                "x",
                "footprint",
            ),
            optional=("expires_at",) if data["version"] >= 2 else (),
            context="saved object",
        )
        token, definition_id = row["id"], row["definition_id"]
        if (
            not isinstance(token, str)
            or not re.fullmatch(r"object_[1-9][0-9]*", token)
            or token in ids
            or not isinstance(definition_id, str)
            or definition_id not in definitions_by_id
        ):
            raise ValueError("Invalid saved World identity")
        if int(token.removeprefix("object_")) >= next_id:
            raise ValueError("World ID counter would reuse an instance")
        footprint = ObjectFootprint(*_pair(row["footprint"]))
        position = WorldPosition(_number(row["x"]), 0)
        if not surface.contains(position, footprint):
            raise ValueError("Saved World object is out of bounds")
        if (
            row.get("expires_at") is not None
            and ObjectInteraction.READ
            not in definitions_by_id[definition_id].interactions
        ):
            raise ValueError("Only books expire")
        ids.add(token)
        objects.append(
            WorldObjectSnapshot(
                token,
                definition_id,
                _integer(row["revision"]),
                ObjectState.RESTING,
                position,
                footprint,
                expires_at=(
                    None
                    if row.get("expires_at") is None
                    else _number(row["expires_at"])
                ),
            )
        )
    if next_id < 1:
        raise ValueError("Invalid next World ID")
    return WorldSnapshot(surface, revision, definitions, tuple(objects), next_id)
