"""Narrow visual effects granted to a game; never rules or pet movement."""

from collections.abc import Callable
from dataclasses import dataclass

FrameMarker = Callable[[int], None]
Completed = Callable[[], None]


@dataclass(frozen=True, slots=True)
class GamePresentation:
    action: Callable[[str, int, FrameMarker, Completed], None]
    cancel: Callable[[], None]
    look: Callable[[tuple[float, float] | None], None]
