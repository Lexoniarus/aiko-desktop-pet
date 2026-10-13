"""Pure per-clip timing policy shared by asset generation and runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .animation import FRAME_COUNTS

REGULAR_CLIPS = frozenset(FRAME_COUNTS) - {"look"}


@dataclass(frozen=True, slots=True)
class AnimationTimingPolicy:
    """All eight holds within a clip match; different clips may differ."""

    regular_frames: int
    gaze_directions: int
    frame_ms: Mapping[str, int]

    def duration_for(self, state: str) -> int:
        if state not in self.frame_ms:
            raise ValueError(f"Unknown regular animation: {state}")
        return self.frame_ms[state]


def load_timing_policy(root: Path) -> AnimationTimingPolicy:
    """Reject incomplete profiles before a player or asset export uses them."""
    data = json.loads((root / "animation_timing.json").read_text("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid animation timing policy")
    holds = data.get("frame_duration_ms")
    if (
        data.get("version") != 2
        or data.get("regular_frames") != 8
        or data.get("gaze_directions") != 16
        or not isinstance(holds, dict)
        or set(holds) != REGULAR_CLIPS
        or any(type(ms) is not int or not 40 <= ms <= 1000
               for ms in holds.values())
    ):
        raise ValueError("Invalid per-clip animation timing policy")
    return AnimationTimingPolicy(
        regular_frames=8, gaze_directions=16,
        frame_ms=MappingProxyType(dict(holds)),
    )
