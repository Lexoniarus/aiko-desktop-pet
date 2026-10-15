"""Validated per-frame pacing and optional sprite replay sequences."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ..catalog_validation import object_fields
from .animation import FRAME_COUNTS

REGULAR_CLIPS = frozenset(FRAME_COUNTS) - {"look"}
# Playback-only actions reuse their source clip's PNGs and pose durations.
VIRTUAL_CLIPS: Mapping[str, str] = MappingProxyType(
    {
        "waving-greeting": "waving",
    }
)


@dataclass(frozen=True, slots=True)
class AnimationTimingPolicy:
    """Eight source sprites per clip; playback may reuse existing sprites."""

    regular_frames: int
    gaze_directions: int
    frame_ms: Mapping[str, tuple[int, ...]]
    sequences: Mapping[str, tuple[int, ...]]

    def duration_for(self, state: str, index: int) -> int:
        if state not in self.frame_ms:
            raise ValueError(f"Unknown regular animation: {state}")
        return self.frame_ms[state][index]

    def sequence_for(self, state: str) -> tuple[int, ...]:
        if state not in self.sequences:
            raise ValueError(f"Unknown regular animation: {state}")
        return self.sequences[state]


def parse_timing_policy(data: object) -> AnimationTimingPolicy:
    object_fields(
        data,
        (
            "version",
            "regular_frames",
            "gaze_directions",
            "frame_duration_ms",
            "frame_sequences",
        ),
        context="animation timing",
    )
    """Validate decoded timing data without filesystem or UI dependencies."""
    if not isinstance(data, dict):
        raise ValueError("Invalid animation timing policy")
    holds = data.get("frame_duration_ms")
    custom = data.get("frame_sequences")
    if (
        type(data.get("version")) is not int
        or data.get("version") != 3
        or type(data.get("regular_frames")) is not int
        or type(data.get("gaze_directions")) is not int
        or data.get("regular_frames") != 8
        or data.get("gaze_directions") != 16
        or not isinstance(holds, dict)
        or set(holds) != REGULAR_CLIPS
        or not isinstance(custom, dict)
        or not set(custom).issubset(REGULAR_CLIPS | frozenset(VIRTUAL_CLIPS))
        or not set(VIRTUAL_CLIPS).issubset(custom)
    ):
        raise ValueError("Invalid per-frame animation timing policy")
    frames: dict[str, tuple[int, ...]] = {}
    sequences: dict[str, tuple[int, ...]] = {}
    expected = set(range(8))
    for state in REGULAR_CLIPS | frozenset(VIRTUAL_CLIPS):
        if state in REGULAR_CLIPS:
            values = holds[state]
            if (
                not isinstance(values, list)
                or len(values) != 8
                or any(type(ms) is not int or not 40 <= ms <= 5000 for ms in values)
            ):
                raise ValueError(f"Invalid frame durations: {state}")
            frames[state] = tuple(values)
        raw_order = custom.get(state, list(range(8)))
        if (
            not isinstance(raw_order, list)
            or not 8 <= len(raw_order) <= 32
            or any(
                type(index) is not int or index not in expected for index in raw_order
            )
            or set(raw_order) != expected
            or raw_order[0] != 0
            or raw_order[-1] != 7
        ):
            raise ValueError(f"Invalid playback sequence: {state}")
        sequences[state] = tuple(raw_order)
    return AnimationTimingPolicy(
        regular_frames=8,
        gaze_directions=16,
        frame_ms=MappingProxyType(frames),
        sequences=MappingProxyType(sequences),
    )
