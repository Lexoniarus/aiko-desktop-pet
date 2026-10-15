"""Turn sampled pointer coordinates into existing cursor motion evidence.

Desktop input owns OS sampling, PetMind owns attention history, and this
application component observes a position without any Tk or UI side effects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..pet.mind.cursor_attention import CursorAttention


@dataclass(frozen=True, slots=True)
class CursorMotion:
    """Only the distance and screen width required by the existing policy."""

    distance: float
    screen_width: int
    now: float


class CursorObservation:
    """Connect a pointer sample to PetMind's session attention clock."""

    def __init__(self, attention: CursorAttention) -> None:
        self.attention = attention

    def observe(
        self, pointer: tuple[int, int], now: float, *,
        game_mode: bool, eyes: tuple[float, float],
        screen_width: int,
    ) -> CursorMotion | None:
        """Report only actual changes; game samples update the baseline."""
        if not self.attention.observe(pointer, now, game_mode=game_mode):
            return None
        return CursorMotion(
            distance=math.hypot(pointer[0] - eyes[0], pointer[1] - eyes[1]),
            screen_width=screen_width,
            now=now,
        )
