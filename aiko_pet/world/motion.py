"""Analytic item motion in World units; positive vertical velocity points up."""

from __future__ import annotations

import math


def contact_time(height: float, velocity: float, gravity: float) -> float:
    """Next descending contact, including an upward launch from ground level."""
    if (not all(math.isfinite(v) for v in (height, velocity, gravity))
            or height < 0 or gravity <= 0):
        raise ValueError("Invalid ballistic values")
    root = math.sqrt(velocity * velocity + 2 * gravity * height)
    # Avoid cancellation for a fast descending item close to the ground.
    return ((velocity + root) / gravity if velocity >= 0
            else 2 * height / (root - velocity))


def flight(height: float, velocity: float, elapsed: float, gravity: float
           ) -> tuple[float, float]:
    """Advance no further than contact; callers own the collision response."""
    contact = contact_time(height, velocity, gravity)
    if not math.isfinite(elapsed) or elapsed < 0 or elapsed > contact + 1e-9:
        raise ValueError("Flight interval crosses ground contact")
    return (max(0.0, height + velocity * elapsed - gravity * elapsed**2 / 2),
            velocity - gravity * elapsed)
