"""Validate the shared HD Waiting clip, with the legacy atlas as fallback."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..pet.animation.character import AnimationClip, AnimationFrame
from ..pet.catalog_validation import integer_value, load_json, object_fields

WAITING_REST = "expressions/rest-neutral/00.png"


def load_hd_waiting_clip(root: Path) -> Mapping[str, AnimationClip]:
    path = root / "actions/waiting.json"
    if not path.is_file():
        return MappingProxyType({})
    data = object_fields(load_json(path), ("version", "size", "anchor", "frames"),
                         context="HD Waiting clip")
    if (type(data["version"]) is not int or data["version"] != 1
            or data["size"] != [384, 416] or data["anchor"] != [96, 194]):
        raise ValueError("Invalid HD Waiting version, size or floor anchor")
    rows = data["frames"]
    if not isinstance(rows, list) or not 2 <= len(rows) <= 120:
        raise ValueError("Expected a bounded HD Waiting sequence")
    frames: list[AnimationFrame] = []
    checked: dict[Path, str] = {}
    asset_root = root.resolve()
    for row in rows:
        record = object_fields(row, ("file", "duration_ms", "sha256"),
                               context="HD Waiting frame")
        relative = record["file"]
        if not isinstance(relative, str) or (
            relative != WAITING_REST
            and re.fullmatch(r"actions/waiting/[a-z0-9_-]+\.png", relative) is None
        ):
            raise ValueError("Invalid HD Waiting frame path")
        source = (asset_root / relative).resolve()
        if not source.is_relative_to(asset_root) or not source.is_file():
            raise ValueError("Missing or unsafe HD Waiting frame")
        if source not in checked:
            checked[source] = hashlib.sha256(source.read_bytes()).hexdigest()
        if checked[source] != record["sha256"]:
            raise ValueError("HD Waiting frame digest mismatch")
        duration = integer_value(record["duration_ms"], minimum=1, maximum=5000,
                                 context="HD Waiting frame duration")
        frames.append(AnimationFrame(source, duration))
    rest = (asset_root / WAITING_REST).resolve()
    if (frames[0].file != rest or frames[-1].file != rest
            or sum(frame.duration_ms for frame in frames) > 30_000):
        raise ValueError("HD Waiting must be bounded and start and end in neutral Idle")
    return MappingProxyType({
        "waiting": AnimationClip("waiting", tuple(frames), True, (96, 194),
                                 rest_sway=True),
    })
