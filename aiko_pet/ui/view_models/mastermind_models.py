"""Only visible code slots, and pure desktop placement of their strip."""

from dataclasses import dataclass

from ..common.window_geometry import WindowBounds
from .game_models import HandAnchor


@dataclass(frozen=True, slots=True)
class CodeView:
    slots: tuple[str | None, ...] = (None,) * 4


@dataclass(frozen=True, slots=True)
class CodeLayout:
    x: int
    y: int
    scale: int


def place_code(anchor: HandAnchor, occupied: tuple[WindowBounds, ...]) -> CodeLayout:
    bounds = WindowBounds(anchor.left, anchor.top, anchor.right, anchor.bottom)
    scale = 2 if anchor.scale == 2 and bounds.width >= 416 else 1
    width, height, gap = 208 * scale, 88 * scale, 10
    y = anchor.y + anchor.height * 2 // 3 - height // 2
    candidates = (
        (anchor.x + anchor.width + gap, y),
        (anchor.x - width - gap, y),
        (anchor.x + (anchor.width - width) // 2, anchor.y + anchor.height + gap),
        (anchor.x + (anchor.width - width) // 2, anchor.y - height - gap),
    )
    pet = WindowBounds(
        anchor.x, anchor.y, anchor.x + anchor.width, anchor.y + anchor.height
    )

    def overlap(x: int, y: int, other: WindowBounds) -> int:
        return max(0, min(x + width, other.right) - max(x, other.left)) * max(
            0, min(y + height, other.bottom) - max(y, other.top)
        )

    placed = tuple(bounds.clamp(x, y, width, height) for x, y in candidates)
    x, y = min(
        placed,
        key=lambda p: overlap(p[0], p[1], pet) * 10
        + sum(overlap(p[0], p[1], other) for other in occupied),
    )
    return CodeLayout(x, y, scale)
