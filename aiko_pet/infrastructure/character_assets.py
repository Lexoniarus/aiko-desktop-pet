"""Decode prepared character metadata without creating Tk images or timers."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Any

from ..asset_paths import ASSET_ROOT
from ..pet.animation.character import (
    FRAME_HEIGHT,
    FRAME_WIDTH,
    AnimationClip,
    AnimationFrame,
    CharacterCatalog,
)
from ..pet.animation.timing import VIRTUAL_CLIPS
from ..pet.catalog_validation import load_json, object_fields
from .animation_timing import load_timing_policy


def _file(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("A sprite requires a relative file path")
    path = (root / value).resolve()
    if Path(value).is_absolute() or not path.is_relative_to(root.resolve()):
        raise ValueError("Sprite path escapes its asset directory")
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def load_character_catalog(root: Path = ASSET_ROOT) -> CharacterCatalog:
    """Validate the complete catalog before the desktop creates its widgets."""
    data = object_fields(
        load_json(root / "animations.json"),
        ("version", "frame_size", "animations"),
        context="animations",
    )
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported character catalog version")
    policy = load_timing_policy(root)
    if not isinstance(data, dict) or data.get("frame_size") != [
        FRAME_WIDTH,
        FRAME_HEIGHT,
    ]:
        raise ValueError("Unsupported character frame dimensions")
    entries = data.get("animations")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Missing character animations")
    clips: dict[str, AnimationClip] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid animation entry")
        object_fields(
            entry,
            ("state", "loop", "anchor", "frames"),
            optional=(
                "return_to",
                "sequence",
                "playback_total_ms",
                "frame_size",
                "source_anchor",
                "total_ms",
                "original_total_ms",
                "new_frame_count",
                "attack_side",
                "effect_direction",
                "effects_embedded",
                "external_hand_embedded",
                "food_embedded",
                "overlay",
                "overlays",
                "release_event",
                "release_frame",
                "transition_included",
                "weapon_embedded",
            ),
            context="animation entry",
        )
        name, loop, anchor = (
            entry.get("state"),
            entry.get("loop"),
            entry.get("anchor"),
        )
        if not isinstance(name, str) or not name or name in clips:
            raise ValueError("Missing or duplicate animation name")
        if type(loop) is not bool:
            raise ValueError("Animation loop must be boolean")
        if (
            not isinstance(anchor, list)
            or len(anchor) != 2
            or any(type(value) is not int for value in anchor)
            or not 0 <= anchor[0] <= FRAME_WIDTH
            or not 0 <= anchor[1] <= FRAME_HEIGHT
        ):
            raise ValueError("Invalid character anchor")
        raw_frames = entry.get("frames")
        if not isinstance(raw_frames, list) or not raw_frames:
            raise ValueError("Animation requires frames")
        frames: list[AnimationFrame] = []
        for frame in raw_frames:
            if not isinstance(frame, dict):
                raise ValueError("Invalid animation frame")
            object_fields(
                frame,
                ("file", "duration_ms"),
                optional=(
                    "source_duration_ms",
                    "events",
                    "food_anchor",
                    "hand_foreground",
                    "degrees_clockwise_from_up",
                    "spell_anchor",
                    "weapon_anchor",
                    "weapon_angle_deg",
                ),
                context=f"animation {name} frame",
            )
            duration = frame.get("duration_ms")
            events = frame.get("events", [])
            if type(duration) is not int or not 1 <= duration <= 60_000:
                raise ValueError("Invalid frame duration")
            if not isinstance(events, list) or any(
                not isinstance(event, str) or not event for event in events
            ):
                raise ValueError("Invalid frame events")
            raw_food_anchor = frame.get("food_anchor")
            food_anchor: tuple[int, int] | None = None
            if raw_food_anchor is not None:
                if (
                    not isinstance(raw_food_anchor, list)
                    or len(raw_food_anchor) != 2
                    or any(type(value) is not int for value in raw_food_anchor)
                    or not 0 <= raw_food_anchor[0] <= FRAME_WIDTH
                    or not 0 <= raw_food_anchor[1] <= FRAME_HEIGHT
                ):
                    raise ValueError("Invalid food hand anchor")
                food_anchor = (raw_food_anchor[0], raw_food_anchor[1])
            frames.append(
                AnimationFrame(
                    _file(root, frame.get("file")),
                    duration,
                    tuple(events),
                    food_anchor=food_anchor,
                )
            )
        if name != "look":
            if len(frames) != policy.regular_frames:
                raise ValueError(f"{name} must have eight animation frames")
            if tuple(frame.duration_ms for frame in frames) != policy.frame_ms[name]:
                raise ValueError(f"{name} differs from configured frame timing")
            order = entry.get("sequence")
            if (
                not isinstance(order, list)
                or any(type(index) is not int for index in order)
                or order != list(policy.sequence_for(name))
            ):
                raise ValueError(f"{name} has an invalid playback sequence")
            playback_order = policy.sequence_for(name)
            if entry.get("playback_total_ms") != sum(
                frames[index].duration_ms for index in playback_order
            ):
                raise ValueError(f"{name} has an invalid playback duration")
        else:
            if "sequence" in entry:
                raise ValueError("Look poses are fixed, not sequenced")
            playback_order = ()
        return_to = entry.get("return_to", "idle")
        if not isinstance(return_to, str):
            raise ValueError("Invalid return animation")
        clips[name] = AnimationClip(
            name,
            tuple(frames),
            loop,
            (anchor[0], anchor[1]),
            return_to,
            playback_order,
        )
    for variant, source_name in VIRTUAL_CLIPS.items():
        if variant in clips or source_name not in clips:
            raise ValueError(f"Invalid playback variant: {variant}")
        source = clips[source_name]
        clips[variant] = AnimationClip(
            variant,
            source.frames,
            source.loop,
            source.anchor,
            source.return_to,
            policy.sequence_for(variant),
        )
    for required in ("idle", "sleep", "eat", "petting", "look"):
        if required not in clips:
            raise ValueError(f"Missing required animation: {required}")
    if len(clips["look"].frames) != policy.gaze_directions:
        raise ValueError("Cursor gaze requires sixteen direction poses")
    if any(clip.return_to not in clips for clip in clips.values()):
        raise ValueError("Unknown return animation")
    return CharacterCatalog(MappingProxyType(clips))
