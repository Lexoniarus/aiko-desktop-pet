"""Read animation timing JSON and delegate validation to pure pet policy."""

from __future__ import annotations

import json
from pathlib import Path

from ..pet.animation.timing import AnimationTimingPolicy, parse_timing_policy


def load_timing_policy(root: Path) -> AnimationTimingPolicy:
    """Read one timing profile without mutating any pet animation state."""
    data = json.loads((root / "animation_timing.json").read_text("utf-8"))
    return parse_timing_policy(data)
