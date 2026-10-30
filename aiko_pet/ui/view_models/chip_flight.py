"""Pure public geometry for one ballistic arc clearing the board."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChipTarget:
    x: float
    y: float
    left: float
    right: float
    top: float
    size: float = 48


def flight_height(start: tuple[float, float], target: ChipTarget) -> float:
    dx, dy = target.x - start[0], target.y - start[1]
    height = abs(dy) * .55 + 60
    if start[0] < target.left or start[0] > target.right:
        for i in range(1, 100):
            t = i / 100
            x, size = start[0] + dx * t, 32 + (target.size - 32) * t
            if x + size / 2 >= target.left and x - size / 2 <= target.right:
                needed = (start[1] + dy * t + size / 2 - target.top
                          + 14 * (1 - t)) / (4 * t * (1 - t))
                height = max(height, needed)
    return height


def flight_point(
    fraction: float, start: tuple[float, float], target: ChipTarget,
) -> tuple[float, float]:
    t, height = fraction, flight_height(start, target)
    return (start[0] + (target.x - start[0]) * t,
            start[1] + (target.y - start[1]) * t - 4 * height * t * (1 - t))
