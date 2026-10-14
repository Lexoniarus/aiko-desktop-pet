"""Explicit commands and immutable read values for the single care toolbar."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..view_models.contracts import (
    HoverAnchor as HoverAnchor,
    HoverSnapshot as HoverSnapshot,
)


@dataclass(frozen=True, slots=True)
class HoverActions:
    """Only the capabilities a hover panel is allowed to call."""

    interact: Callable[[str], None]
    toggle_pin: Callable[[], None]
    open_settings: Callable[[int, int], None]
    save_position: Callable[[int | None, int | None], None]
    move_speech: Callable[[], None]
    restore_stack: Callable[[], bool]
