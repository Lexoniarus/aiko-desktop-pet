"""Read optional baked HD body poses without changing the legacy atlas."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..pet.animation.character import AnimationClip, AnimationFrame
from ..pet.catalog_validation import load_json, object_fields

BODY_CLIP_COUNTS = {
    "body-turn-left": 5, "body-turn-right": 5,
    "body-look-left": 9, "body-look-right": 9,
}


def load_body_pose_clips(root: Path) -> Mapping[str, AnimationClip]:
    """Legacy/fixture installations without this optional pack stay valid."""
    path = root / "body_poses" / "manifest.json"
    if not path.is_file():
        return MappingProxyType({})
    data = object_fields(
        load_json(path), ("version", "size", "clips"),
        optional=("sources",), context="body pose pack",
    )
    if data["version"] != 1 or data["size"] != [384, 416]:
        raise ValueError("Invalid body pose version or dimensions")
    raw_clips = data["clips"]
    if not isinstance(raw_clips, dict) or set(raw_clips) != set(BODY_CLIP_COUNTS):
        raise ValueError("Incomplete body orientation pack")
    clips: dict[str, AnimationClip] = {}
    for name, count in BODY_CLIP_COUNTS.items():
        paths = raw_clips[name]
        if not isinstance(paths, list) or len(paths) != count:
            raise ValueError(f"Invalid body pose count: {name}")
        frames: list[AnimationFrame] = []
        for value in paths:
            if not isinstance(value, str) or Path(value).is_absolute():
                raise ValueError("Body pose path must be relative")
            candidate = (root / value).resolve()
            if not candidate.is_relative_to(root.resolve()):
                raise ValueError("Body pose path escapes asset directory")
            if not candidate.is_file():
                raise FileNotFoundError(candidate)
            frames.append(AnimationFrame(candidate, 140))
        clips[name] = AnimationClip(name, tuple(frames), False, (95, 194))
    return MappingProxyType(clips)
