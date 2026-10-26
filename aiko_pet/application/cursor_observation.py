"""Turn sampled pointer coordinates into existing cursor motion evidence.

Desktop input owns OS sampling, PetMind owns attention history, and this
application component observes a position without any Tk or UI side effects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..pet.mind.cursor_attention import CursorAttention, CursorPerception


@dataclass(frozen=True, slots=True)
class CursorMotion:
    """Only the distance and screen width required by the existing policy."""

    distance: float
    screen_width: int
    now: float


@dataclass(frozen=True, slots=True)
class CursorObservationResult:
    """Every sample provides evidence; only changed positions emit remarks."""

    perception: CursorPerception
    motion: CursorMotion | None


class CursorObservation:
    """Connect a pointer sample to PetMind's session attention clock."""

    def __init__(self, attention: CursorAttention) -> None:
        self.attention = attention
        self.current = CursorPerception()

    def observe(
        self,
        pointer: tuple[int, int],
        now: float,
        *,
        game_mode: bool,
        eyes: tuple[float, float],
        screen_width: int,
        scale: int = 1,
    ) -> CursorObservationResult:
        """Report only actual changes; game samples update the baseline."""
        width = 192.0 * max(1, scale)
        moved = self.attention.observe(
            pointer,
            now,
            game_mode=game_mode,
            width=width,
        )
        dx, dy = pointer[0] - eyes[0], pointer[1] - eyes[1]
        distance = math.hypot(dx, dy)
        vx, vy = self.attention.velocity
        gap_x = max(0.0, abs(dx) - width * 0.34)
        gap_y = max(0.0, -dy - width * 0.18, dy - width * 0.58)
        self.current = CursorPerception(
            now,
            pointer,
            math.hypot(gap_x, gap_y) / width,
            math.hypot(vx, vy) / width,
            -(vx * dx + vy * dy) / max(1.0, distance) / width,
            max(0.0, now - self.attention.stationary_since),
            1 if dx > width * 0.05 else -1 if dx < -width * 0.05 else 0,
            width * 0.28 <= dy <= width * 0.75,
            self.attention.valid,
        )
        motion = (
            CursorMotion(
                distance=math.hypot(pointer[0] - eyes[0], pointer[1] - eyes[1]),
                screen_width=screen_width,
                now=now,
            )
            if moved
            else None
        )
        return CursorObservationResult(self.current, motion)
