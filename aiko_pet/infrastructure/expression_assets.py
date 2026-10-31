"""Validate the optional, baked V3 facial/rest pack outside the legacy atlas."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..pet.animation.character import AnimationClip, AnimationFrame
from ..pet.animation.expression import EXPRESSION_CLIPS
from ..pet.catalog_validation import load_json, object_fields


def load_expression_clips(root: Path) -> Mapping[str, AnimationClip]:
    path = root / "expressions" / "manifest.json"
    if not path.is_file():
        return MappingProxyType({})
    data = object_fields(load_json(path), ("version", "size", "clips"),
                         context="expression pack")
    if type(data["version"]) is not int or data["version"] != 1 or (
        data["size"] != [384, 416]
    ):
        raise ValueError("Invalid expression pack version or dimensions")
    rows = data["clips"]
    if not isinstance(rows, dict) or set(rows) != set(EXPRESSION_CLIPS.values()):
        raise ValueError("Incomplete expression pack")
    clips: dict[str, AnimationClip] = {}
    for name, row in rows.items():
        row = object_fields(row, ("frames", "anchor"), context="expression clip")
        anchor = row["anchor"]
        if (not isinstance(anchor, list) or len(anchor) != 2
                or any(type(n) is not int for n in anchor)
                or not 0 <= anchor[0] <= 192 or not 0 <= anchor[1] <= 208):
            raise ValueError("Invalid expression anchor")
        records = row["frames"]
        if not isinstance(records, list) or len(records) != 8:
            raise ValueError("Expression requires eight source phases")
        frames: list[AnimationFrame] = []
        for index, record in enumerate(records):
            record = object_fields(record, ("file", "duration_ms", "sha256",
                                            "source_sha256"),
                                   context="expression frame")
            relative, duration, digest = (
                record["file"], record["duration_ms"], record["sha256"],
            )
            if (relative != f"expressions/{name}/{index:02}.png"
                    or type(duration) is not int or not 0 < duration <= 10000
                    or not isinstance(digest, str)
                    or re.fullmatch(r"[a-f0-9]{64}", digest) is None
                    or not isinstance(record["source_sha256"], str)
                    or re.fullmatch(r"[a-f0-9]{64}", record["source_sha256"]) is None):
                raise ValueError("Invalid expression frame")
            source = (root / relative).resolve()
            if not source.is_relative_to(root.resolve()) or not source.is_file():
                raise ValueError("Missing or unsafe expression frame")
            if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                raise ValueError("Expression frame digest mismatch")
            frames.append(AnimationFrame(source, duration))
        clips[name] = AnimationClip(name, tuple(frames), False, tuple(anchor),
                                    rest_sway=True)
    return MappingProxyType(clips)
