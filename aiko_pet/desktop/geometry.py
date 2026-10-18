"""Pure taskbar-aligned position and sprite clamping, no native calls."""

from __future__ import annotations

from dataclasses import dataclass

FOOT_BASELINE = 194


def item_face_offset(
    pointer: tuple[float, float], *, pivot: tuple[float, float],
    size: tuple[int, int], eyes: tuple[float, float], width: float,
) -> tuple[float, float]:
    """Displayed item center relative to the existing eyes, in sprite widths."""
    if width <= 0:
        raise ValueError("Sprite width must be positive")
    return ((pointer[0] - pivot[0] + size[0] / 2 - eyes[0]) / width,
            (pointer[1] - pivot[1] + size[1] / 2 - eyes[1]) / width)


@dataclass(frozen=True)
class GroundApproach:
    """A bounded full-window standing position for ordinary ground reach."""

    standing_x: int

    def arrived(self, x: float) -> bool:
        return abs(x - self.standing_x) <= 2


@dataclass(frozen=True)
class TaskbarTrack:
    """Primary-monitor horizontal route; coordinates are screen pixels."""

    left: int
    right: int
    ground_y: int

    def clamp_x(self, x: float, sprite_width: int) -> int:
        """Keep the full sprite window horizontally inside the walking track."""
        maximum = max(self.left, self.right - sprite_width)
        return max(self.left, min(round(x), maximum))

    def sprite_y(self, scale: int) -> int:
        """Place the sprite's feet at the taskbar, not its transparent margin."""
        return max(0, self.ground_y - FOOT_BASELINE * scale)

    def ground_inset(self, sprite_width: int, reach: float) -> float:
        """Reachable anchor margin in World coordinates, independent of origin."""
        return min((self.right - self.left) / 2,
                   max(0, sprite_width / 2 - reach))

    def ground_approach(
        self, object_x: float, sprite_width: int, reach: float,
    ) -> GroundApproach | None:
        """Resolve the closest full-window pose on this supported ground track."""
        if (sprite_width <= 0 or self.right - self.left < sprite_width
                or not self.left <= object_x <= self.right):
            return None
        standing_x = self.clamp_x(object_x - sprite_width / 2, sprite_width)
        residual = abs(object_x - (standing_x + sprite_width / 2))
        return GroundApproach(standing_x) if residual <= reach else None

    def can_grasp_ground(
        self, object_x: float, pet_x: float, sprite_width: int, reach: float,
    ) -> bool:
        """Require a reachable anchor, ordinary distance and an on-track pet."""
        approach = self.ground_approach(object_x, sprite_width, reach)
        if (approach is None
                or not self.left <= pet_x <= self.right - sprite_width):
            return False
        return abs(object_x - (pet_x + sprite_width / 2)) <= reach
