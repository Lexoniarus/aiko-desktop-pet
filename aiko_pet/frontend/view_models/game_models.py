"""Detached game graphics and pure placement; no hidden card information."""

from dataclasses import dataclass

from ...games.blackjack import Table
from ...games.playing_cards import Card


@dataclass(frozen=True, slots=True)
class HandView:
    cards: tuple[Card | None, ...] = ()


def project_dealer_hand(table: Table) -> HandView:
    return HandView(table.dealer)


@dataclass(frozen=True, slots=True)
class HandAnchor:
    x: int
    y: int
    width: int
    height: int
    left: int
    top: int
    right: int
    bottom: int
    scale: int


@dataclass(frozen=True, slots=True)
class HandLayout:
    x: int
    y: int
    width: int
    height: int
    step: int


def place_hand(
    count: int, anchor: HandAnchor, *, caption_height: int = 22,
) -> HandLayout:
    card = 128
    step = min(48, max(
        1, (anchor.right - anchor.left - card) // max(1, count - 1),
    ))
    width = card + max(0, count - 1) * step
    height = card + 16 + caption_height
    x = max(anchor.left, min(
        anchor.x - width - 12, anchor.right - width,
    ))
    y = max(anchor.top, min(
        anchor.y + 38 * anchor.scale, anchor.bottom - height,
    ))
    return HandLayout(x, y, width, height, step)
