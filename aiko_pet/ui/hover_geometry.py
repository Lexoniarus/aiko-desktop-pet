"""Pure geometry rules for hover placement, dragging and pointer bridges."""

from __future__ import annotations

from dataclasses import dataclass

from ..presentation.contracts import HoverAnchor


@dataclass(frozen=True, slots=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


class HoverGeometry:
    """Screen-space hover layout without any Tk, state or application access."""

    @staticmethod
    def placement(
        anchor: HoverAnchor, panel_width: int, panel_height: int,
        screen_width: int, screen_height: int,
    ) -> tuple[int, int]:
        if anchor.pinned_x is not None and anchor.pinned_y is not None:
            x, y = anchor.pinned_x, anchor.pinned_y
        else:
            right_x = anchor.x + anchor.width + 10
            left_x = anchor.x - panel_width - 10
            x = (
                right_x if right_x + panel_width <= screen_width
                else left_x
            )
            y = anchor.y + max(0, (anchor.height - panel_height) // 2)
        return (
            max(0, min(round(x), max(0, screen_width - panel_width))),
            max(0, min(round(y), max(0, screen_height - panel_height))),
        )

    @staticmethod
    def bridge(
        px: int, py: int, panel: Rect, sprite: Rect, *,
        pinned: bool,
    ) -> bool:
        """Preserve the narrow gap that allows cursor movement onto the UI."""
        if pinned:
            return False
        bar_right = panel.x + panel.width
        sprite_right = sprite.x + sprite.width
        top = max(panel.y, sprite.y)
        bottom = min(panel.y + panel.height, sprite.y + sprite.height)
        if top <= bottom:
            if bar_right <= sprite.x:
                return (
                    bar_right - 3 <= px <= sprite.x + 5
                    and top <= py <= bottom
                )
            if sprite_right <= panel.x:
                return (
                    sprite_right - 5 <= px <= panel.x + 3
                    and top <= py <= bottom
                )
        left = max(panel.x, sprite.x)
        right = min(bar_right, sprite_right)
        if left <= right:
            return (
                left <= px <= right
                and panel.y + panel.height - 3 <= py <= sprite.y + 10
            )
        return False

    @staticmethod
    def dragged(
        start: tuple[int, int, int, int],
        pointer: tuple[int, int],
        panel_size: tuple[int, int],
        screen_size: tuple[int, int],
    ) -> tuple[int, int]:
        px, py, x, y = start
        width, height = panel_size
        screen_width, screen_height = screen_size
        return (
            max(0, min(x + pointer[0] - px, max(0, screen_width - width))),
            max(0, min(y + pointer[1] - py, max(0, screen_height - height))),
        )
