"""Taskbar walk planning without Tkinter side effects.

The desktop GUI is solely responsible for applying clamped window geometry.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from ..desktop.geometry import TaskbarTrack


@dataclass(frozen=True)
class WalkConditions:
    """Values needed to decide whether and how far Aiko should move."""

    now: float
    elapsed_seconds: float
    x: float
    track: TaskbarTrack
    sprite_width: int
    energy: float
    auto_walk: bool
    sleeping: bool
    attention_active: bool
    toolbar_visible: bool
    observing_computer: bool
    computer_busy: bool
    quiet_period: bool


@dataclass(frozen=True)
class WalkStep:
    """Requested horizontal displacement and matching sprite animation."""

    pixels: float
    animation: str


class WalkController:
    """Own walking distance, direction and next departure time."""

    def __init__(self, *, next_walk_at: float = 0.0) -> None:
        self.remaining_distance = 0.0
        self.next_walk_at = next_walk_at

    def plan_step(self, conditions: WalkConditions) -> WalkStep | None:
        """Prepare one step, respecting work, hover, sleep and energy."""
        now = conditions.now
        if conditions.observing_computer and conditions.computer_busy:
            self.remaining_distance = 0.0
            self.next_walk_at = max(self.next_walk_at, now + 2)
            return None

        if (
            not conditions.auto_walk
            or conditions.sleeping
            or conditions.attention_active
            or conditions.toolbar_visible
        ):
            self.remaining_distance = 0.0
            return None

        if self.remaining_distance == 0 and now >= self.next_walk_at:
            interval = (
                random.uniform(12, 24) if conditions.quiet_period
                else random.uniform(4, 9)
            )
            self.next_walk_at = now + interval
            if conditions.energy >= 20:
                limit = conditions.track.right - conditions.sprite_width
                if conditions.x <= conditions.track.left + 80:
                    direction = 1
                elif conditions.x >= limit - 80:
                    direction = -1
                else:
                    direction = random.choice((-1, 1))
                self.remaining_distance = direction * random.randint(100, 320)

        if self.remaining_distance == 0:
            return None
        direction = 1 if self.remaining_distance > 0 else -1
        pixels = direction * min(
            abs(self.remaining_distance),
            max(1.0, 64 * conditions.elapsed_seconds),
        )
        animation = "running-right" if direction > 0 else "running-left"
        return WalkStep(pixels=pixels, animation=animation)

    def record_displacement(self, moved_pixels: float) -> bool:
        """Consume actual clamped movement; return true when walking stops."""
        self.remaining_distance -= moved_pixels
        if moved_pixels == 0 or abs(self.remaining_distance) < 1:
            self.remaining_distance = 0.0
            return True
        return False
