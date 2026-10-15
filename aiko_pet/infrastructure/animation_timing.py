"""Read animation timing JSON and delegate validation to pure pet policy."""

from __future__ import annotations

from pathlib import Path

from ..pet.animation.timing import AnimationTimingPolicy, parse_timing_policy
from ..pet.catalog_validation import load_json


def load_timing_policy(root: Path) -> AnimationTimingPolicy:
    """Read one timing profile without mutating any pet animation state."""
    data = load_json(root / "animation_timing.json")
    return parse_timing_policy(data)
