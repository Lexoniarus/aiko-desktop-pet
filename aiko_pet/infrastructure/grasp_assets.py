"""Validated optional V3 grasp family; originals remain outside the package."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..pet.animation.character import AnimationClip, AnimationFrame
from ..pet.catalog_validation import load_json, object_fields

GRASP_CLIPS = frozenset({
    "pick_up", "hold_item", "put_down", "inspect_item", "inspect_hold",
    "inspect_return", "throw_item",
})


def load_grasp_clips(root: Path) -> Mapping[str, AnimationClip]:
    path = root / "actions/grasp.json"
    if not path.is_file():
        return MappingProxyType({})
    data = object_fields(load_json(path), ("version", "size", "anchor", "clips"),
                         context="grasp family")
    if (type(data["version"]) is not int or data["version"] != 1
            or data["size"] != [384, 416] or data["anchor"] != [96, 194]
            or not isinstance(data["clips"], dict)
            or set(data["clips"]) != GRASP_CLIPS):
        raise ValueError("Invalid V3 grasp family header")
    result: dict[str, AnimationClip] = {}
    checked: dict[Path, str] = {}
    allowed = {
        "pick_up": {"attach_object"}, "put_down": {"detach_object"},
        "throw_item": {"attach_object", "release_object"},
        "inspect_item": {"inspect_comment", "inspect_emote"},
    }
    for name, definition in data["clips"].items():
        definition = object_fields(definition, ("frames", "hold_last"),
                                   context=f"grasp {name}")
        rows = definition["frames"]
        if (not isinstance(rows, list) or not 1 <= len(rows) <= 300
                or type(definition["hold_last"]) is not bool):
            raise ValueError("Invalid grasp sequence")
        frames: list[AnimationFrame] = []
        markers: list[str] = []
        for row in rows:
            row = object_fields(row, ("file", "duration_ms", "sha256",
                                      "food_anchor", "events"), context=name)
            relative, duration, digest = row["file"], row["duration_ms"], row["sha256"]
            if (not isinstance(relative, str)
                    or re.fullmatch(r"actions/grasp/[a-z0-9_-]+\.png", relative) is None
                    or type(duration) is not int or not 1 <= duration <= 5000
                    or not isinstance(digest, str)
                    or re.fullmatch(r"[a-f0-9]{64}", digest) is None):
                raise ValueError("Invalid grasp frame path, duration or digest")
            source = (root / relative).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                raise ValueError("Missing or unsafe grasp frame")
            if source not in checked:
                checked[source] = hashlib.sha256(source.read_bytes()).hexdigest()
            if checked[source] != digest:
                raise ValueError("Grasp source hash mismatch")
            events = row["events"]
            if (not isinstance(events, list)
                    or any(not isinstance(e, str) or e not in allowed.get(name, set())
                           for e in events)):
                raise ValueError("Invalid grasp marker")
            anchor = row["food_anchor"]
            if anchor is not None and (
                not isinstance(anchor, list) or len(anchor) != 2
                or any(type(n) is not int for n in anchor)
                or not 0 <= anchor[0] <= 192 or not 0 <= anchor[1] <= 208
            ):
                raise ValueError("Invalid grasp palm position")
            markers.extend(events)
            frames.append(AnimationFrame(source, duration, tuple(events),
                                         tuple(anchor) if anchor is not None else None))
        if sorted(markers) != sorted(allowed.get(name, set())):
            raise ValueError("Grasp markers must occur exactly once")
        if sum(f.duration_ms for f in frames) > 30000:
            raise ValueError("Unbounded grasp sequence")
        result[name] = AnimationClip(
            name, tuple(frames), False, (96, 194),
            hold_last=definition["hold_last"], item_anchor_mode="center",
        )
    if (round(result["inspect_item"].duration_seconds * 1000) != 2550
            or round(result["inspect_hold"].duration_seconds * 1000) != 1000
            or round(result["inspect_return"].duration_seconds * 1000) != 450):
        raise ValueError("Grasp inspection must retain its four-second movement")
    return MappingProxyType(result)
