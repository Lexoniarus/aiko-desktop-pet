"""Pure sprite priorities and animation frame timing.

This module does not depend on Tkinter or the desktop window manager.
"""

from __future__ import annotations

from dataclasses import dataclass

FRAME_COUNTS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
    "look": 16,
}
FRAME_TIMINGS = {
    "idle": 0.38,
    "running-left": 0.13,
    "running-right": 0.13,
    "waving": 0.22,
    "jumping": 0.18,
    "failed": 0.33,
    "waiting": 0.42,
    "running": 0.22,
    "review": 0.3,
}


@dataclass(frozen=True)
class SpriteSelection:
    """Animation name and optional fixed sprite index."""

    animation: str
    fixed_frame: int | None = None


def choose_passive_animation(
    *,
    gaze_direction: int | None,
    observing_computer: bool,
    computer_busy: bool,
    energy: float,
    mood: float,
    satiety: float,
) -> SpriteSelection:
    """Choose the highest-priority ambient sprite with no GUI side effects."""
    if gaze_direction is not None:
        return SpriteSelection("look", fixed_frame=gaze_direction)
    if observing_computer and computer_busy:
        return SpriteSelection("review")
    if energy < 10 or mood < 10:
        return SpriteSelection("failed")
    if satiety < 20 or energy < 24:
        return SpriteSelection("waiting")
    return SpriteSelection("idle")


class FrameClock:
    """Own frame progress while the GUI only renders the selected PNG."""

    def __init__(self, *, started_at: float = 0.0) -> None:
        self.active_key: tuple[str, int | None] | None = None
        self.frame_index = 0
        self.frame_started_at = started_at

    def next_index(
        self,
        animation: str,
        now: float,
        frame_count: int,
        *,
        fixed: int | None = None,
    ) -> int:
        """Advance at most one frame per call, matching the former GUI timer."""
        if frame_count < 1:
            raise ValueError("An animation needs at least one frame")
        if fixed is not None and not 0 <= fixed < frame_count:
            raise IndexError("Fixed animation frame is out of range")
        key = animation, fixed
        if key != self.active_key:
            self.active_key = key
            self.frame_index = 0
            self.frame_started_at = now
        elif fixed is None and now - self.frame_started_at >= FRAME_TIMINGS.get(
            animation, 0.3,
        ):
            self.frame_index = (self.frame_index + 1) % frame_count
            self.frame_started_at = now
        return fixed if fixed is not None else self.frame_index
