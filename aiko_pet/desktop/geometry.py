"""Pure taskbar-aligned position and sprite clamping, no native calls."""

from __future__ import annotations

from dataclasses import dataclass

FOOT_BASELINE = 194


@dataclass(frozen=True)
class GroundApproach:
    """A bounded standing position and its required kind of ground grip."""

    standing_x: int
    edge_grip: bool

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

    def ground_approach(
        self, object_x: float, sprite_width: int, reach: float,
    ) -> GroundApproach | None:
        """Resolve the closest full-window pose on this supported ground track."""
        if (sprite_width <= 0 or self.right - self.left < sprite_width
                or not self.left <= object_x <= self.right):
            return None
        standing_x = self.clamp_x(object_x - sprite_width / 2, sprite_width)
        residual = abs(object_x - (standing_x + sprite_width / 2))
        edge = standing_x in (self.left, self.right - sprite_width)
        return GroundApproach(standing_x, edge_grip=edge and residual > reach)

    def can_grasp_ground(
        self, object_x: float, pet_x: float, sprite_width: int, reach: float,
    ) -> bool:
        """Allow ordinary reach, or a bounded edge grip after actual arrival."""
        approach = self.ground_approach(object_x, sprite_width, reach)
        if (approach is None
                or not self.left <= pet_x <= self.right - sprite_width):
            return False
        if approach.edge_grip:
            return approach.arrived(pet_x)
        return abs(object_x - (pet_x + sprite_width / 2)) <= reach
