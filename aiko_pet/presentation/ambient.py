"""Small autonomous gestures while Aiko is genuinely idle.

An idle blink is a complete eight-frame animation, followed by a neutral
resting pose. Brief independent gaze choices use the existing sixteen static
directional sprites without hijacking mouse tracking or dialogue scheduling.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence

from .animation import SpriteSelection

_DIRECTIONS = (2, 3, 4, 12, 13, 14)


class AmbientDirector:
    """Pure policy for blink gaps, quiet poses and occasional self-glances."""

    def __init__(
        self, started_at: float, *,
        between: Callable[[float, float], float] = random.uniform,
        direction: Callable[[Sequence[int]], int] = random.choice,
    ) -> None:
        self._between = between
        self._direction = direction
        self._blink_active = False
        self._glance_frame: int | None = None
        self._glance_until = started_at
        self.next_blink_at = started_at + self._between(5.0, 11.0)
        self.next_glance_at = started_at + self._between(22.0, 46.0)

    @property
    def blinking(self) -> bool:
        return self._blink_active

    def suspend(self, now: float) -> None:
        """Cancel ambient activity while sleeping, walking or interacting."""
        self._blink_active = False
        self._glance_frame = None
        self._glance_until = now
        self.next_blink_at = now + self._between(5.0, 11.0)
        self.next_glance_at = now + self._between(22.0, 46.0)

    def choose(self, now: float) -> SpriteSelection:
        """Return one stable look pose, active blink or neutral idle rest."""
        if self._blink_active:
            return SpriteSelection("idle")

        if self._glance_frame is not None:
            if now < self._glance_until:
                return SpriteSelection("look", fixed_frame=self._glance_frame)
            self._glance_frame = None
            self.next_glance_at = now + self._between(22.0, 46.0)

        if now >= self.next_glance_at:
            index = self._direction(_DIRECTIONS)
            if index not in _DIRECTIONS:
                raise ValueError("Invalid autonomous glance direction")
            self._glance_frame = index
            self._glance_until = now + self._between(1.1, 2.2)
            return SpriteSelection("look", fixed_frame=index)

        if now >= self.next_blink_at:
            self._blink_active = True
            return SpriteSelection("idle")
        return SpriteSelection("idle", fixed_frame=0)

    def finish_blink(self, now: float) -> None:
        """A full eight-frame blink ended; do not immediately repeat it."""
        if self._blink_active:
            self._blink_active = False
            self.next_blink_at = now + self._between(5.0, 11.0)
