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
    speed_pixels_per_second: float
    stride_pixels: float
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
        self._residual = 0.0
        self._requested = 0.0
        self._blocked = False
        self._quiet = False

    def pause(self, now: float) -> None:
        """Begin a complete rest interval at the actual end of a walk."""
        self.remaining_distance = 0.0
        self._residual = 0.0
        self.next_walk_at = now + random.uniform(120 if self._quiet else 60, 180)

    def interrupt(self) -> None:
        """Resume with a full pause after the blocking activity ends."""
        self.remaining_distance = 0.0
        self._residual = 0.0
        self._blocked = True

    def plan_step(self, conditions: WalkConditions) -> WalkStep | None:
        """Prepare one step, respecting work, hover, sleep and energy."""
        now = conditions.now
        self._quiet = conditions.quiet_period
        if (
            conditions.attention_active and self.remaining_distance == 0
            and conditions.auto_walk and not conditions.sleeping
            and not conditions.toolbar_visible
            and not (conditions.observing_computer and conditions.computer_busy)
        ):
            # Brief cursor attention postpones departure, not the entire rest.
            return None
        if (
            (conditions.observing_computer and conditions.computer_busy)
            or not conditions.auto_walk
            or conditions.sleeping
            or conditions.attention_active
            or conditions.toolbar_visible
        ):
            self.interrupt()
            return None
        if self._blocked:
            self._blocked = False
            self.pause(now)
            return None

        if self.remaining_distance == 0 and now >= self.next_walk_at:
            if conditions.energy >= 20:
                limit = conditions.track.right - conditions.sprite_width
                if conditions.x <= conditions.track.left + 80:
                    direction = 1
                elif conditions.x >= limit - 80:
                    direction = -1
                else:
                    direction = random.choice((-1, 1))
                self.remaining_distance = (
                    direction * random.randint(2, 4) * conditions.stride_pixels
                )
                self.next_walk_at = float("inf")
            else:
                self.pause(now)

        if self.remaining_distance == 0:
            return None
        direction = 1 if self.remaining_distance > 0 else -1
        pixels = direction * min(
            abs(self.remaining_distance),
            max(0.0, conditions.speed_pixels_per_second * conditions.elapsed_seconds),
        )
        if conditions.elapsed_seconds > 0:
            pixels += self._residual
        self._requested = pixels
        animation = "running-right" if direction > 0 else "running-left"
        return WalkStep(pixels=pixels, animation=animation)

    def record_displacement(
        self, moved_pixels: float, *, now: float, blocked: bool = False,
    ) -> bool:
        """Consume actual clamped movement; return true when walking stops."""
        self.remaining_distance -= moved_pixels
        self._residual = self._requested - moved_pixels
        if blocked or abs(self.remaining_distance) < 1:
            self.pause(now)
            return True
        return False
