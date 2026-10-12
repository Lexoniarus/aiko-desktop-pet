"""Validation and normalization of saved values and simulation bounds."""

from __future__ import annotations

import math
from typing import Any

def clamp_saved_time(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    return number if math.isfinite(number) and 0 <= number <= 4_000_000_000 else 0.0


def bounded(value: Any, default: float = 75.0) -> float:
    """Convert malformed saved values to a safe 0..100 number."""
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    if not math.isfinite(result):
        return default
    return max(0.0, min(100.0, result))
