"""Pure daily-routine and streaming elapsed-time planning for the aggregate.

Policies calculate transitions and time steps; PetState owns every mutation.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from .balance import BALANCE
from .food import FoodActivity
from .routine import TimeContext, context_at
from .sleep import SleepContext, SleepEpisode, sleep_transition

# Live telemetry is never projected across a restart/suspend or offline gap.
MAX_LIVE_EFFORT_SECONDS = BALANCE.number("simulation", "maximum_live_effort_seconds")


class RoutineValues(Protocol):
    """Read-only routine inputs for the pure transition policy."""

    @property
    def sleeping(self) -> bool: ...

    @property
    def sleep_origin(self) -> str: ...

    @property
    def nap_until(self) -> float: ...

    @property
    def auto_sleep_night(self) -> str: ...

    @property
    def auto_nap_day(self) -> str: ...

    @property
    def energy(self) -> float: ...

    @property
    def lived_seconds(self) -> float: ...

    @property
    def sleep_episode(self) -> SleepEpisode: ...


@dataclass(frozen=True, slots=True)
class RoutineTransition:
    """Calculated sleep/routine fields, without changing the input pet."""

    sleeping: bool
    sleep_origin: str
    nap_until: float
    auto_sleep_night: str
    auto_nap_day: str
    episode: SleepEpisode


@dataclass(frozen=True, slots=True)
class SimulationStep:
    """One authoritative elapsed interval, with calendar anchors for scheduling."""

    elapsed_start: float
    elapsed_end: float
    wall_start: float
    wall_end: float
    context: TimeContext | None
    effort: float | None
    food_activity: FoodActivity | None = None
    observed: bool = False

    def __post_init__(self) -> None:
        if (any(not math.isfinite(v) for v in (
            self.elapsed_start, self.elapsed_end, self.wall_start, self.wall_end,
        )) or self.elapsed_start < 0 or self.elapsed_end <= self.elapsed_start
                or self.wall_end < self.wall_start):
            raise ValueError("Invalid simulation interval")

    @property
    def seconds(self) -> float:
        return self.elapsed_end - self.elapsed_start

    @property
    def hours(self) -> float:
        """A rate-conversion view, never the source of an elapsed endpoint."""
        return self.seconds / 3600


@dataclass(frozen=True, slots=True)
class TimePlan:
    """Full elapsed duration with constant-memory iteration, never an age cap."""

    now: float
    elapsed_seconds: float
    elapsed_start: float
    auto_routine: bool
    effort: float | None
    food_activity: FoodActivity | None

    @property
    def elapsed_end(self) -> float:
        return self.elapsed_start + self.elapsed_seconds

    def __iter__(self) -> Iterator[SimulationStep]:
        offset = 0.0
        known_since = max(0.0, self.elapsed_seconds - MAX_LIVE_EFFORT_SECONDS)
        while offset < self.elapsed_seconds:
            wall = self.now - (self.elapsed_seconds - offset)
            end = self.elapsed_seconds
            if self.auto_routine:
                # Align the grid across calls instead of drifting after restart.
                step_seconds = BALANCE.number("simulation", "needs_step_seconds")
                boundary = (math.floor(wall / step_seconds) + 1) * step_seconds
                end = min(end, offset + (boundary - wall))
            if offset < known_since < end:
                end = known_since
            observed = offset >= known_since
            start_elapsed = self.elapsed_start + offset
            end_elapsed = self.elapsed_start + end
            if end_elapsed > start_elapsed:
                yield SimulationStep(
                    elapsed_start=start_elapsed, elapsed_end=end_elapsed,
                    wall_start=wall, wall_end=self.now - (self.elapsed_seconds - end),
                    context=context_at(wall) if self.auto_routine else None,
                    effort=self.effort if observed else None,
                    food_activity=self.food_activity if observed else None,
                    observed=observed,
                )
            offset = end


def calculate_daily_routine(
    record: RoutineValues,
    context: TimeContext,
    *,
    allow_bedtime: bool = True,
    allow_nap: bool = False,
    interrupt_nap: bool = False,
    effort: float | None = None,
    sleep_context: SleepContext | None = None,
    automatic: bool = True,
) -> RoutineTransition:
    """Apply sleep priorities; legacy routine fields remain compatibility reads."""
    observation = sleep_context or SleepContext.permissions(
        allow_bedtime, allow_nap, interrupt_nap,
    )
    result = sleep_transition(
        record.sleep_episode, sleeping=record.sleeping, energy=record.energy,
        elapsed=record.lived_seconds, wall=context.local.timestamp(),
        context=observation, automatic=automatic,
    )
    origin = {"main": "routine", "nap": "nap", "recovery": "recovery"}.get(
        result.episode.kind, "",
    ) if result.sleeping else ""
    return RoutineTransition(
        result.sleeping, origin,
        result.episode.wake_wall if origin == "nap" else 0.0,
        context.night_key if origin == "routine" else record.auto_sleep_night,
        context.day_key if origin == "nap" else record.auto_nap_day,
        result.episode,
    )


def plan_pet_time(
    updated_at: float,
    now: float,
    *,
    auto_routine: bool = False,
    effort: float | None = None,
    elapsed_seconds: float | None = None,
    elapsed_start: float = 0.0,
    food_activity: FoodActivity | None = None,
) -> TimePlan | None:
    """Plan all elapsed time; current observations cover only a recent tail."""
    if not math.isfinite(now):
        return None
    duration = now - updated_at if elapsed_seconds is None else elapsed_seconds
    if not math.isfinite(duration):
        return None
    elapsed = max(0.0, duration)
    if (not math.isfinite(elapsed_start) or elapsed_start < 0
            or not math.isfinite(elapsed_start + elapsed)):
        raise ValueError("Invalid pet elapsed-time interval")
    if type(effort) not in (int, float):
        effort = None
    elif effort is not None and (not math.isfinite(effort) or not 0.0 <= effort <= 1.0):
        effort = None
    return TimePlan(now, elapsed, elapsed_start, auto_routine, effort, food_activity)
