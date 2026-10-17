"""Versioned subjective records; technical save provenance is not perception."""

from __future__ import annotations

import math
import re
from dataclasses import asdict
from typing import Any, cast

from ..pet.catalog_validation import object_fields
from ..pet.mind.object_knowledge import (
    ObjectMemorySnapshot,
    PlaceStatus,
    SavedObjectKnowledge,
)
from ..pet.mind.object_perception import ConsumableKind


def encode_object_memory(
    snapshot: ObjectMemorySnapshot, *, world_next_id: int = 1,
) -> dict[str, Any]:
    entries = []
    for item in snapshot.entries:
        row = asdict(item)
        row["possible_sources"] = list(item.possible_sources)
        entries.append(row)
    return {"version": 2, "entries": entries,
            "next_record_id": snapshot.next_record_id,
            "world_next_id": world_next_id}


def _number(raw: Any) -> float:
    if type(raw) not in (int, float) or not math.isfinite(raw) or raw < 0:
        raise ValueError("Invalid object memory numeric value")
    return float(raw)


def _counter(raw: Any) -> int:
    if type(raw) is not int or raw < 1:
        raise ValueError("Invalid memory allocation counter")
    return raw


def decode_object_memory(
    raw: Any, identities: dict[str, ConsumableKind], *,
    allocated_until: int | None = None,
) -> ObjectMemorySnapshot:
    """Read v1 history or v2 records without joining them to current objects."""
    if not isinstance(raw, dict) or type(raw.get("version")) is not int:
        raise ValueError("Invalid object memory version")
    version = raw["version"]
    if version not in (1, 2):
        raise ValueError("Unsupported object memory version")
    fields = ("version", "entries") + (
        ("next_record_id", "world_next_id") if version == 2 else ()
    )
    data = object_fields(raw, fields, context="saved object memory")
    next_id = _counter(data["next_record_id"]) if version == 2 else 1
    if version == 2:
        watermark = _counter(data["world_next_id"])
        if allocated_until is not None and watermark > allocated_until:
            raise ValueError("Memory belongs to an older World allocation")
    if not isinstance(data["entries"], list):
        raise ValueError("Object memory entries must be a list")
    entries: list[SavedObjectKnowledge] = []
    tokens: set[str] = set()
    for entry in data["entries"]:
        names = ("token", "identity", "kind", "x", "height", "resting",
                 "age_seconds", "disposition") + (
            ("assessed", "place_status", "possible_sources") if version == 2
            else ("examined",)
        )
        row = object_fields(entry, names, context="remembered object")
        token, identity, kind = row["token"], row["identity"], row["kind"]
        if (not isinstance(token, str) or not re.fullmatch(
            r"(?:object|memory)_[1-9][0-9]*" if version == 2
            else r"object_[1-9][0-9]*", token,
        ) or token in tokens):
            raise ValueError("Invalid subjective record ID")
        if (version == 1 and allocated_until is not None
                and int(token.removeprefix("object_")) >= allocated_until):
            raise ValueError("Unallocated legacy memory ID")
        if (token.startswith("memory_")
                and int(token.removeprefix("memory_")) >= next_id):
            raise ValueError("Memory record ID would be reused")
        if identity is None:
            if kind is not None:
                raise ValueError("Unknown identity cannot have a known kind")
        elif (not isinstance(identity, str) or identity not in identities
              or kind != identities[identity]):
            raise ValueError("Invalid remembered catalog identity")
        assessed = row["assessed" if version == 2 else "examined"]
        if type(row["resting"]) is not bool or type(assessed) is not bool:
            raise ValueError("Remembered flags require booleans")
        disposition = row["disposition"]
        if disposition not in (None, "deferred", "interrupted"):
            raise ValueError("Invalid remembered disposition")
        if (assessed and identity is None
                or disposition == "deferred" and not assessed):
            raise ValueError("Remembered experience requires learned identity")
        status = row["place_status"] if version == 2 else "remembered"
        sources = row["possible_sources"] if version == 2 else []
        if status not in ("remembered", "missing", "superseded"):
            raise ValueError("Invalid remembered place status")
        if (not isinstance(sources, list)
                or any(not isinstance(source, str) for source in sources)
                or len(set(sources)) != len(sources) or token in sources):
            raise ValueError("Invalid subjective association")
        entries.append(SavedObjectKnowledge(
            token, identity, kind, _number(row["x"]), _number(row["height"]),
            row["resting"], _number(row["age_seconds"]), assessed, disposition,
            cast(PlaceStatus, status), tuple(sources),
        ))
        tokens.add(token)
    by_token = {item.token: item for item in entries}
    resolved: set[str] = set()
    pending = dict(by_token)
    for item in entries:
        for source in item.possible_sources:
            other = by_token.get(source)
            if (other is None or item.identity is None
                    or (other.identity, other.kind) != (item.identity, item.kind)):
                raise ValueError("Invalid association reference/type")
    while pending:
        ready = [key for key, item in pending.items()
                 if set(item.possible_sources) <= resolved]
        if not ready:
            raise ValueError("Cyclic subjective associations")
        for key in ready:
            resolved.add(key)
            del pending[key]
    return ObjectMemorySnapshot(tuple(entries), next_id)
