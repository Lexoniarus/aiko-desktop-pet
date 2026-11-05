"""Validate the optional baked HD meal; nutrition remains in application care."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..pet.animation.character import AnimationClip, AnimationFrame
from ..pet.catalog_validation import load_json, object_fields


def load_hd_eating_clip(root: Path) -> Mapping[str, AnimationClip]:
    """Legacy installations retain their existing eight-frame eating clip."""
    path = root / "actions" / "eat.json"
    if not path.is_file():
        return MappingProxyType({})
    data = object_fields(load_json(path), ("version", "size", "anchor", "frames"),
                         context="HD eating clip")
    if (type(data["version"]) is not int or data["version"] != 1
            or data["size"] != [384, 416] or data["anchor"] != [96, 194]):
        raise ValueError("Invalid HD eating version, size or floor anchor")
    rows = data["frames"]
    if not isinstance(rows, list) or not 13 <= len(rows) <= 300:
        raise ValueError("HD eating requires a bounded complete sequence")
    frames: list[AnimationFrame] = []
    bites = 0
    hidden = False
    total = 0
    checked: dict[Path, str] = {}
    for row in rows:
        row = object_fields(row, ("file", "duration_ms", "sha256", "food_anchor",
                                  "events"), context="HD eating frame")
        relative, duration, digest = row["file"], row["duration_ms"], row["sha256"]
        if (not isinstance(relative, str)
                or re.fullmatch(r"actions/eat/[a-z0-9_-]+\.png", relative) is None
                or type(duration) is not int or not 1 <= duration <= 5000
                or not isinstance(digest, str)
                or re.fullmatch(r"[a-f0-9]{64}", digest) is None):
            raise ValueError("Invalid HD eating frame path, time or hash")
        source = (root / relative).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file():
            raise ValueError("Missing or unsafe HD eating frame")
        if source not in checked:
            checked[source] = hashlib.sha256(source.read_bytes()).hexdigest()
        if checked[source] != digest:
            raise ValueError("HD eating frame hash mismatch")
        events = row["events"]
        if events not in ([], ["bite"]):
            raise ValueError("Invalid HD eating event")
        bites += len(events)
        anchor = row["food_anchor"]
        if anchor is not None and (
            not isinstance(anchor, list) or len(anchor) != 2
            or any(type(n) is not int for n in anchor)
            or not 0 <= anchor[0] <= 192 or not 0 <= anchor[1] <= 208
        ):
            raise ValueError("Invalid HD eating food anchor")
        if hidden and anchor is not None:
            raise ValueError("Consumed food must not reappear")
        if anchor is None:
            if bites != 3:
                raise ValueError("Food must remain until the third bite")
            hidden = True
        total += duration
        frames.append(AnimationFrame(
            source, duration, tuple(events),
            food_anchor=tuple(anchor) if anchor is not None else None,
        ))
    if bites != 3 or not hidden or not 5000 <= total <= 30000:
        raise ValueError("HD eating requires three bites and a finite finish")
    return MappingProxyType({
        "eat": AnimationClip("eat", tuple(frames), False, (96, 194)),
    })
