"""Narrow visual effects granted to a game; never rules or pet movement."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

FrameMarker = Callable[[int], None]
Completed = Callable[[], None]


@dataclass(frozen=True, slots=True)
class GamePresentation:
    action: Callable[[str, int | tuple[int, ...], FrameMarker, Completed], None]
    cancel: Callable[[], None]
    look: Callable[[tuple[float, float] | None], None]
    origin: Callable[[], tuple[float, float, int]] = lambda: (0, 0, 1)
    configure: Callable[[tk.Toplevel], None] = lambda _: None
    configure_control: Callable[[tk.Toplevel], None] = lambda _: None
