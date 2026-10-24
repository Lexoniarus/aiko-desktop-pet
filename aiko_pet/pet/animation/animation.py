"""Pure sprite priorities and animation frame timing.

This module does not depend on Tkinter or the desktop window manager.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..balance import BALANCE

FRAME_COUNTS: dict[str, int] = dict.fromkeys(
    (
        "idle",
        "running-right",
        "running-left",
        "waving",
        "jumping",
        "failed",
        "waiting",
        "review",
        "sleep",
        "petting",
        "eat",
        "attack",
        "pick_up",
    ),
    8,
)
FRAME_COUNTS["look"] = 16


@dataclass(frozen=True, slots=True)
class PassiveObservation:
    """Pointer gaze and workload facts already gathered by the host."""

    gaze_direction: int | None
    computer_busy: bool
    forward_gaze: bool = False


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
    forward_gaze: bool = False,
) -> SpriteSelection:
    """Choose the highest-priority ambient sprite with no GUI side effects."""
    if gaze_direction is not None:
        return SpriteSelection("look", fixed_frame=gaze_direction)
    if forward_gaze:
        return SpriteSelection("idle", fixed_frame=0)
    if observing_computer and computer_busy:
        return SpriteSelection("review")
    if energy < BALANCE.integer(
        "animation_needs", "critical_energy"
    ) or mood < BALANCE.integer("animation_needs", "critical_mood"):
        return SpriteSelection("failed")
    if satiety < BALANCE.integer(
        "animation_needs", "low_satiety"
    ) or energy < BALANCE.integer("animation_needs", "low_energy"):
        return SpriteSelection("waiting")
    return SpriteSelection("idle")


class FrameClock:
    """Show every authored frame for its hold time without skipping late poses."""

    def __init__(self, *, started_at: float = 0.0) -> None:
        self.active_key: tuple[str, int | None] | None = None
        self.frame_index = 0
        self.frame_started_at = started_at
        self.finished = False
        self.next_delay_ms: int | None = None
        self.end_time = started_at
        self._completed_ms = 0

    def reset(self) -> None:
        """Restart even when two consecutive actions select the same clip."""
        self.active_key = None
        self.finished = False
        self.next_delay_ms = None
        self._completed_ms = 0

    def progress_seconds(self, now: float, timings: tuple[int, ...]) -> float:
        """Authored progress; a late callback cannot consume unseen frames."""
        elapsed = max(0.0, (now - self.frame_started_at) * 1000)
        return (self._completed_ms + min(elapsed, timings[self.frame_index])) / 1000

    def next_index(
        self,
        animation: str,
        now: float,
        timings: tuple[int, ...],
        *,
        fixed: int | None = None,
        loop: bool = True,
    ) -> int:
        if not timings or any(duration <= 0 for duration in timings):
            raise ValueError("An animation needs positive frame durations")
        if fixed is not None and not 0 <= fixed < len(timings):
            raise IndexError("Fixed animation frame is out of range")
        key = animation, fixed
        if key != self.active_key:
            self.active_key = key
            self.frame_index = 0
            self.frame_started_at = now
            self.finished = False
            self._completed_ms = 0
        if fixed is not None:
            self.frame_index = fixed
            self.next_delay_ms = None
            self.end_time = now
            return fixed
        elapsed = max(0.0, (now - self.frame_started_at) * 1000)
        if not self.finished and elapsed + 1e-6 >= timings[self.frame_index]:
            self._completed_ms += timings[self.frame_index]
            if self.frame_index + 1 < len(timings):
                self.frame_index += 1
            elif loop:
                self.frame_index = 0
            else:
                self.finished = True
            # Each newly displayed pose receives its full authored hold time.
            self.frame_started_at = now
            elapsed = 0.0
        if self.finished:
            self.next_delay_ms = None
            self.end_time = now
            return self.frame_index
        remaining = timings[self.frame_index] - elapsed
        self.next_delay_ms = max(1, math.ceil(remaining - 1e-6))
        self.end_time = now + (remaining + sum(timings[self.frame_index + 1 :])) / 1000
        return self.frame_index
