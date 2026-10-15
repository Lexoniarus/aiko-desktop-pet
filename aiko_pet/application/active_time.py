"""Consume active session intervals exactly once, independent of wall time."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from ..pet.food import FoodActivity
from ..pet.state import PetState


@dataclass(frozen=True, slots=True)
class SessionInputs:
    """Trusted time and observed conditions for ticks, care and finished games."""

    wall_time: float
    monotonic_time: float
    auto_routine: bool
    allow_bedtime: bool | None
    allow_nap: bool
    interrupt_nap: bool
    effort: float | None
    food_activity: FoodActivity | None = None


class ActiveSessionClock:
    """The supplied uptime reader excludes system suspend and hibernation."""

    def __init__(self, reader: Callable[[], float | None]) -> None:
        self._reader = reader
        self._anchor = self._sample()

    def _sample(self) -> float | None:
        value = self._reader()
        return value if value is not None and math.isfinite(value) else None

    def consume(self) -> float:
        """Reset after unavailable/backward readings rather than invent time."""
        previous, current = self._anchor, self._sample()
        self._anchor = current
        if previous is None or current is None:
            return 0.0
        return max(0.0, current - previous)


def advance_session_time(
    state: PetState, clock: ActiveSessionClock, inputs: SessionInputs,
) -> None:
    """Consume one shared interval and forward the full live-time contract."""
    state.advance(
        inputs.wall_time,
        auto_routine=inputs.auto_routine,
        allow_bedtime=inputs.allow_bedtime,
        allow_nap=inputs.allow_nap,
        interrupt_nap=inputs.interrupt_nap,
        effort=inputs.effort,
        elapsed_seconds=clock.consume(),
        food_activity=inputs.food_activity,
    )
