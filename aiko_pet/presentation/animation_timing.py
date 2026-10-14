"""Compatibility loader for callers of the original presentation path.

Validation lives in pet.animation.timing; production filesystem access is
owned by infrastructure.animation_timing instead.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..pet.animation.timing import (
    AnimationTimingPolicy as AnimationTimingPolicy,
    REGULAR_CLIPS as REGULAR_CLIPS,
    VIRTUAL_CLIPS as VIRTUAL_CLIPS,
    parse_timing_policy,
)


def load_timing_policy(root: Path) -> AnimationTimingPolicy:
    """Compatibility facade with no duplicate validation rules."""
    data = json.loads((root / "animation_timing.json").read_text("utf-8"))
    return parse_timing_policy(data)
