"""Pure game-window placement inside a monitor's usable rectangle."""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True, slots=True)
class WindowBounds:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(1, self.right - self.left)

    @property
    def height(self) -> int:
        return max(1, self.bottom - self.top)

    def clamp(self, x: int, y: int, width: int, height: int) -> tuple[int, int]:
        return (
            max(self.left, min(x, self.right - width)),
            max(self.top, min(y, self.bottom - height)),
        )


BoundsAt = Callable[[int, int], WindowBounds]


def beside_character(
    x: int, y: int, pet_width: int, pet_height: int,
    width: int, height: int, bounds: WindowBounds,
) -> tuple[int, int]:
    """Prefer right, then left; if neither side fits, use the roomier side."""
    gap = 12
    right, left = x + pet_width + gap, x - width - gap
    if right + width <= bounds.right:
        target = right
    elif left >= bounds.left:
        target = left
    else:
        target = right if bounds.right - right >= x - bounds.left else left
    return bounds.clamp(target, y + (pet_height - height) // 2, width, height)
