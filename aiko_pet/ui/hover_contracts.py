"""Explicit hover callbacks; legacy view-model imports remain compatible."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..application.view_models import (
    HoverAnchor as HoverAnchor,
    HoverSnapshot as HoverSnapshot,
)


@dataclass(frozen=True, slots=True)
class HoverActions:
    """Only the capabilities a hover panel is allowed to call."""

    interact: Callable[[str], None]
    open_status: Callable[[], None]
    open_settings: Callable[[int, int], None]
    save_position: Callable[[int | None, int | None], None]
    move_speech: Callable[[], None]
    restore_stack: Callable[[], bool]
