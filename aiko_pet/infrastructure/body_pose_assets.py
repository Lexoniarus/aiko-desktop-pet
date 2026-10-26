"""Read optional baked HD body poses without changing the legacy atlas."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from ..pet.animation.character import AnimationClip, AnimationFrame
from ..pet.catalog_validation import load_json, object_fields

BODY_CLIP_COUNTS = {
    "body-turn-left": 5,
    "body-turn-right": 5,
    "body-look-left": 9,
    "body-look-right": 9,
}


def load_body_pose_clips(root: Path) -> Mapping[str, AnimationClip]:
    """Legacy/fixture installations without this optional pack stay valid."""
    path = root / "body_poses" / "manifest.json"
    if not path.is_file():
        return MappingProxyType({})
    data = object_fields(
        load_json(path),
        ("version", "size", "clips"),
        optional=("sources", "locomotion"),
        context="body pose pack",
    )
    if (
        type(data["version"]) is not int
        or data["version"] not in (1, 2)
        or data["size"] != [384, 416]
    ):
        raise ValueError("Invalid body pose version or dimensions")
    raw_clips = data["clips"]
    motion = data.get("locomotion", {})
    if not isinstance(motion, dict):
        raise ValueError("Invalid locomotion metadata")
    if not isinstance(raw_clips, dict) or set(raw_clips) != set(BODY_CLIP_COUNTS) | set(
        motion
    ):
        raise ValueError("Incomplete body orientation pack")
    clips: dict[str, AnimationClip] = {}
    for name in [*BODY_CLIP_COUNTS, *sorted(motion)]:
        meta = motion.get(name)
        durations = [140] * BODY_CLIP_COUNTS.get(name, 0)
        if meta is not None:
            meta = object_fields(
                meta,
                ("kind", "heading", "gaze", "durations", "family", "stride"),
                context="locomotion clip",
            )
            count = 6 if meta["kind"] == "step" else 9
            durations = meta["durations"]
            if (
                meta["kind"] not in ("step", "turn")
                or meta["heading"] not in (-1, 1)
                or not isinstance(durations, list)
                or len(durations) != count
                or any(type(v) is not int or v <= 0 for v in durations)
                or not isinstance(meta["family"], str)
                or type(meta["stride"]) not in (int, float)
                or meta["stride"] < 0
                or (
                    meta["gaze"] is not None
                    and (type(meta["gaze"]) is not int or not 0 <= meta["gaze"] < 16)
                )
            ):
                raise ValueError("Invalid locomotion clip")
        count = len(durations)
        paths = raw_clips[name]
        if not isinstance(paths, list) or len(paths) != count:
            raise ValueError(f"Invalid body pose count: {name}")
        frames: list[AnimationFrame] = []
        for index, value in enumerate(paths):
            if not isinstance(value, str) or Path(value).is_absolute():
                raise ValueError("Body pose path must be relative")
            candidate = (root / value).resolve()
            if not candidate.is_relative_to(root.resolve()):
                raise ValueError("Body pose path escapes asset directory")
            if not candidate.is_file():
                raise FileNotFoundError(candidate)
            frames.append(AnimationFrame(candidate, durations[index]))
        clips[name] = AnimationClip(
            name,
            tuple(frames),
            bool(meta is not None and meta["kind"] == "step"),
            (95, 194),
            movement=meta is not None and meta["kind"] == "step",
            family=meta["family"] if meta is not None else "",
            heading=meta["heading"] if meta is not None else 0,
            head_direction=meta["gaze"] if meta is not None else None,
            stride=float(meta["stride"]) if meta is not None else 0,
        )
    return MappingProxyType(clips)
