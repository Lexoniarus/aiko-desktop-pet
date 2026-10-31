"""Explicit commands and immutable read values for the single care toolbar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

SelectorCloseReason = Literal["automatic", "navigation", "explicit", "shutdown"]


@dataclass(frozen=True, slots=True)
class HoverActions:
    """Only the capabilities a hover panel is allowed to call."""

    interact: Callable[[str], None]
    toggle_pin: Callable[[], None]
    open_settings: Callable[[int, int], None]
    save_position: Callable[[int | None, int | None], None]
    move_speech: Callable[[], None]
    restore_stack: Callable[[], bool]
    pin_wish: Callable[[int, bool], None] = lambda _id, _pinned: None
    dismiss_wish: Callable[[int], None] = lambda _id: None
    can_interact: Callable[[str], bool] = lambda _action: True
    can_place_item: Callable[[], bool] = lambda: True
