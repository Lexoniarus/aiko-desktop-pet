"""Entire-desktop mouse gazing using 16 original direction sprites."""

from __future__ import annotations

import math

SECTORS = 16
SECTOR_ANGLE = 360 / SECTORS


def angle_distance(a: float, b: float) -> float:
    """Smallest distance between two angles in degrees."""
    return abs((a - b + 180) % 360 - 180)


def gaze_sector(
    eyes_x: float,
    eyes_y: float,
    pointer_x: float,
    pointer_y: float,
    *,
    scale: int = 1,
    previous: int | None = None,
) -> int | None:
    """Return direction, 0=up, 4=right, 8=down, 12=left.

    Mouse coordinates are ABSOLUTE desktop coordinates, including negative
    positions on monitors left/above the primary monitor. There is no maximum
    range: a pointer at the far edge of the desktop is still tracked.
    """
    dx = pointer_x - eyes_x
    dy = pointer_y - eyes_y
    if math.hypot(dx, dy) < 17 * max(1, scale):
        return previous  # Avoid jitter when the pointer is near the eyes.
    angle = math.degrees(math.atan2(dx, -dy)) % 360
    if previous is not None and 0 <= previous < SECTORS:
        # Hold the old sector until the pointer clears the boundary by 3 degrees.
        if angle_distance(angle, previous * SECTOR_ANGLE) <= SECTOR_ANGLE / 2 + 3:
            return previous
    return int(angle / SECTOR_ANGLE + 0.5) % SECTORS
