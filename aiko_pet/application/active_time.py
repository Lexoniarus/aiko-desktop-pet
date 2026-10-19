"""Consume elapsed life time once, including suspend, with explicit fallback."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Protocol

from ..pet.food import FoodActivity
from ..pet.sleep import SleepContext
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
    sleep_context: SleepContext | None = None


class TimeProgression(Protocol):
    def advance(
        self, state: PetState, inputs: SessionInputs, elapsed: float,
    ) -> None: ...


class ActiveSessionClock:
    """Use suspend-inclusive uptime; wall time only bridges unavailable reads.

    Both anchors advance on every consumption so source recovery cannot replay
    a fallback interval. Known uptime wins over wall/DST/manual clock changes.
    """

    def __init__(
        self, reader: Callable[[], float | None],
        *, wall_time: Callable[[], float] | None = None,
    ) -> None:
        self._reader = reader
        self._anchor = self._sample()
        self._wall_anchor = self._finite(wall_time()) if wall_time else None

    @staticmethod
    def _finite(value: float | None) -> float | None:
        return value if value is not None and math.isfinite(value) else None

    def _sample(self) -> float | None:
        value = self._reader()
        return self._finite(value)

    def capture_checkpoint(self) -> tuple[float | None, float | None]:
        return self._anchor, self._wall_anchor

    def restore_checkpoint(
        self, checkpoint: tuple[float | None, float | None],
    ) -> None:
        self._anchor, self._wall_anchor = checkpoint

    def consume(self, *, wall_time: float | None = None) -> float:
        """Consume known elapsed time or a nonnegative wall-clock fallback."""
        previous, current = self._anchor, self._sample()
        previous_wall, current_wall = self._wall_anchor, self._finite(wall_time)
        self._anchor = current
        self._wall_anchor = current_wall
        if previous is not None and current is not None and current >= previous:
            return current - previous
        if previous_wall is not None and current_wall is not None:
            return max(0.0, current_wall - previous_wall)
        return 0.0


def advance_session_time(
    state: PetState, clock: ActiveSessionClock, inputs: SessionInputs,
    *, progression: TimeProgression | None = None,
) -> None:
    """Consume one shared interval and forward the full live-time contract."""
    if not math.isfinite(inputs.wall_time):
        return
    checkpoint = state.capture_checkpoint()
    clock_checkpoint = clock.capture_checkpoint()
    try:
        elapsed = clock.consume(wall_time=inputs.wall_time)
        if progression is not None:
            progression.advance(state, inputs, elapsed)
        else:
            state.advance(
                inputs.wall_time, auto_routine=inputs.auto_routine,
                allow_bedtime=inputs.allow_bedtime, allow_nap=inputs.allow_nap,
                interrupt_nap=inputs.interrupt_nap, effort=inputs.effort,
                elapsed_seconds=elapsed, food_activity=inputs.food_activity,
                sleep_context=inputs.sleep_context,
            )
    except Exception:
        state.restore_checkpoint(checkpoint)
        clock.restore_checkpoint(clock_checkpoint)
        raise
