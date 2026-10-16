"""Strict versioned subjective memory; never join records to live World truth."""

from __future__ import annotations

import math
import re
from dataclasses import asdict
from typing import Any

from ..pet.catalog_validation import object_fields
from ..pet.mind.object_knowledge import ObjectMemorySnapshot, SavedObjectKnowledge
from ..pet.mind.object_perception import ConsumableKind


def encode_object_memory(snapshot: ObjectMemorySnapshot) -> dict[str, Any]:
    entries = []
    for item in snapshot.entries:
        row = asdict(item)
        row["examined"] = row.pop("assessed")
        entries.append(row)
    return {"version": 1, "entries": entries}


def _number(raw: Any) -> float:
    if type(raw) not in (int, float) or not math.isfinite(raw) or raw < 0:
        raise ValueError("Invalid object memory numeric value")
    return float(raw)


def decode_object_memory(
    raw: Any, identities: dict[str, ConsumableKind],
) -> ObjectMemorySnapshot:
    """Validate learned catalog IDs, not membership or locations in current World."""
    data = object_fields(raw, ("version", "entries"), context="saved object memory")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported object memory version")
    if not isinstance(data["entries"], list):
        raise ValueError("Object memory entries must be a list")
    entries: list[SavedObjectKnowledge] = []
    tokens: set[str] = set()
    for entry in data["entries"]:
        row = object_fields(entry, (
            "token", "identity", "kind", "x", "height", "resting", "age_seconds",
            "examined", "disposition",
        ), context="remembered object")
        token, identity, kind = row["token"], row["identity"], row["kind"]
        if (not isinstance(token, str)
                or not re.fullmatch(r"object_[1-9][0-9]*", token) or token in tokens):
            raise ValueError("Invalid remembered instance ID")
        if identity is None:
            if kind is not None:
                raise ValueError("Unknown identity cannot have a known kind")
        elif (not isinstance(identity, str) or identity not in identities
              or kind != identities[identity]):
            raise ValueError("Invalid remembered catalog identity")
        if type(row["resting"]) is not bool or type(row["examined"]) is not bool:
            raise ValueError("Remembered flags require booleans")
        disposition = row["disposition"]
        if disposition not in (None, "deferred", "interrupted"):
            raise ValueError("Invalid remembered disposition")
        if (row["examined"] and identity is None
                or disposition == "deferred" and not row["examined"]):
            raise ValueError("Remembered experience requires learned identity")
        entries.append(SavedObjectKnowledge(
            token, identity, kind, _number(row["x"]), _number(row["height"]),
            row["resting"], _number(row["age_seconds"]), row["examined"], disposition,
        ))
        tokens.add(token)
    return ObjectMemorySnapshot(tuple(entries))
