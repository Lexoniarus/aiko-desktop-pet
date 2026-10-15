"""Pure taskbar-aligned position and sprite clamping, no native calls."""

from __future__ import annotations

from dataclasses import dataclass

FOOT_BASELINE = 194


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
