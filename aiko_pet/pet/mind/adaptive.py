"""Adaptive routine orchestrator driven by observed, bounded local telemetry.

Models and persisted memory contracts live in adaptive_models.py; classification
thresholds live in adaptive_policy.py. The old import names are re-exported.
"""

from __future__ import annotations

import math
from datetime import datetime

from .adaptive_models import (
    DAILY_DECAY as DAILY_DECAY,
    MAX_OBSERVATION_SECONDS as MAX_OBSERVATION_SECONDS,
    SLOTS as SLOTS,
    AdaptiveMemory as AdaptiveMemory,
    Behaviour as Behaviour,
    Observation as Observation,
    _hours as _hours,
    clamp as clamp,
)
from .adaptive_policy import (
    ActivityMode as ActivityMode,
    determine_activity_mode as determine_activity_mode,
    determine_sleep_options as determine_sleep_options,
)
from ..routine import TimeContext, context_at


class AdaptiveRoutine:
    """Pure time-aware state machine driven by coarse 6s observations.

    Wall time sets the schedule. An injected monotonic clock controls elapsed
    exposure, so DST/manual clock changes do not simulate phantom workloads.
    On app restart the next sample establishes a new baseline: no guessing at
    what the PC did while Aiko wasn't running.
    """

    def __init__(self, memory: AdaptiveMemory | None = None) -> None:
        self.memory = memory or AdaptiveMemory()
        self._previous_mono: float | None = None
        self._previous_wall: float | None = None
        self._last_result: Behaviour | None = None

    @staticmethod
    def _slot(context: TimeContext) -> int:
        return context.local.weekday() * 24 + context.local.hour

    def _age_profile(self, today: str) -> None:
        previous = self.memory.profile_day
        if previous == today:
            return
        elapsed = 0
        try:
            if previous:
                elapsed = (datetime.fromisoformat(today).date() -
                           datetime.fromisoformat(previous).date()).days
        except ValueError:
            elapsed = 0
        if elapsed > 0:
            factor = DAILY_DECAY ** min(365, elapsed)
            for series in (self.memory.hour_seconds,
                           self.memory.busy_seconds,
                           self.memory.present_seconds,
                           self.memory.observed_days):
                for index, amount in enumerate(series):
                    series[index] = round(amount * factor, 4)
        self.memory.profile_day = today

    def expected_effort(self, context: TimeContext) -> tuple[float | None, bool]:
        """Require separate observed days; a 72-hour single run isn't 3 weeks."""
        slot = self._slot(context)
        seconds = self.memory.hour_seconds[slot]
        days = self.memory.observed_days[slot]
        if seconds < 900 or days < 1.5:
            return None, False
        return self.memory.busy_seconds[slot] / seconds, days >= 2.5

    def note_interaction(self, now_wall: float) -> None:
        if math.isfinite(now_wall) and now_wall > 0:
            self.memory.last_contact_wall = now_wall

    def forget_profile(self) -> None:
        for series in (self.memory.hour_seconds, self.memory.busy_seconds,
                       self.memory.present_seconds, self.memory.observed_days):
            series[:] = [0.0] * SLOTS
        self.memory.last_slot_key = ""
        self.memory.profile_day = ""

    def _elapsed_observation_seconds(
        self, wall_time: float, monotonic: float,
    ) -> tuple[float | None, float]:
        """Reset stale sessions and ignore suspend/debugger time jumps."""
        previous = self._previous_mono
        if previous is None and self.memory.last_seen_wall:
            # Offline time is never interpreted as observed work or idle time.
            unseen = wall_time - self.memory.last_seen_wall
            if unseen > 1800:
                self.memory.session_seconds = 0.0
                self.memory.rest_seconds = 0.0
                self.memory.settled_work = 0.0
                self.memory.last_session_seconds = 0.0
                self.memory.last_work_wall = 0.0
            if unseen > 6 * 3600:
                self.memory.strain = min(self.memory.strain, 35.0)
        elapsed = 0.0 if previous is None else monotonic - previous
        if not 0 <= elapsed <= 120:
            elapsed = 0.0
        elapsed = min(MAX_OBSERVATION_SECONDS, elapsed)
        self._previous_mono = monotonic
        self._previous_wall = wall_time
        self.memory.last_seen_wall = wall_time
        return previous, elapsed

    def _update_workload_memory(
        self,
        effort: float | None,
        *,
        elapsed: float,
        previous: float | None,
        wall_time: float,
        present: bool | None,
    ) -> None:
        """Smooth work effort and accumulate bounded session/rest exposure."""
        if effort is None:
            return
        alpha = 1.0 - math.exp(-elapsed / 40.0)
        if previous is None:
            self.memory.settled_work = effort
        else:
            self.memory.settled_work += alpha * (
                effort - self.memory.settled_work
            )
        self.memory.settled_work = clamp(self.memory.settled_work, high=1.0)
        if elapsed <= 0:
            return
        if effort >= 0.65:
            self.memory.strain += (effort - 0.45) * elapsed / 3600 * 55
        else:
            self.memory.strain -= (
                max(0.15, 0.65 - effort) * elapsed / 3600 * 38
            )
        self.memory.strain = clamp(self.memory.strain)
        if effort >= 0.65:
            self.memory.session_seconds = min(
                172_800, self.memory.session_seconds + elapsed,
            )
            self.memory.last_work_wall = wall_time
            self.memory.rest_seconds = 0.0
        elif effort < 0.33:
            if self.memory.session_seconds > 0:
                self.memory.last_session_seconds = self.memory.session_seconds
                self.memory.session_seconds = 0.0
            if present is False:
                self.memory.rest_seconds = min(
                    172_800, self.memory.rest_seconds + elapsed,
                )
            else:
                self.memory.rest_seconds = 0.0
        else:
            self.memory.rest_seconds = 0.0

    def _record_hourly_exposure(
        self,
        context: TimeContext,
        *,
        elapsed: float,
        effort: float | None,
        present: bool | None,
        learn: bool,
    ) -> None:
        """Persist aggregates only for actually observed, readable samples."""
        if not learn or elapsed <= 0 or effort is None:
            return
        slot = self._slot(context)
        self.memory.hour_seconds[slot] += elapsed
        self.memory.busy_seconds[slot] += elapsed * effort
        if present is True:
            self.memory.present_seconds[slot] += elapsed
        key = f"{context.day_key}:{context.local.hour:02d}"
        if key != self.memory.last_slot_key:
            self.memory.observed_days[slot] += 1.0
            self.memory.last_slot_key = key

    def observe(
        self,
        observation: Observation,
        monotonic: float,
        *,
        energy: float,
        sleeping: bool,
        manual_sleep: bool = False,
        learn: bool = True,
    ) -> Behaviour:
        """Update measured memory, classify activity and decide rest options."""
        if not math.isfinite(monotonic):
            raise ValueError("monotonic clock must be finite")
        wall_time = observation.wall_time
        context = context_at(wall_time)
        if learn:
            self._age_profile(context.day_key)
        previous, elapsed = self._elapsed_observation_seconds(
            wall_time, monotonic,
        )
        effort = observation.effort
        present = (
            observation.idle_seconds < 300
            if observation.idle_seconds is not None else None
        )
        self._update_workload_memory(
            effort,
            elapsed=elapsed,
            previous=previous,
            wall_time=wall_time,
            present=present,
        )
        self._record_hourly_exposure(
            context, elapsed=elapsed, effort=effort, present=present, learn=learn,
        )
        expected, confident = (
            self.expected_effort(context) if learn else (None, False)
        )
        mode = determine_activity_mode(
            effort=effort,
            settled_work=self.memory.settled_work,
            last_session_seconds=self.memory.last_session_seconds,
            last_work_wall=self.memory.last_work_wall,
            rest_seconds=self.memory.rest_seconds,
            present=present,
            wall_time=wall_time,
        )
        sleep_options = determine_sleep_options(
            mode=mode,
            energy=energy,
            sleeping=sleeping,
            manual_sleep=manual_sleep,
            night=context.night,
            effort=effort,
            idle_seconds=observation.idle_seconds,
            present=present,
            rest_seconds=self.memory.rest_seconds,
            expected_effort=expected,
        )
        result = Behaviour(
            mode=mode,
            strain=self.memory.strain,
            effort=self.memory.settled_work if effort is not None else None,
            expected_effort=expected,
            expectation_confident=confident,
            present=present,
            uptime_hours=observation.uptime_hours,
            prolonged_work_seconds=self.memory.session_seconds,
            rest_seconds=self.memory.rest_seconds,
            can_sleep=sleep_options.can_sleep,
            should_wake=sleep_options.should_wake,
            can_nap=sleep_options.can_nap,
        )
        self._last_result = result
        return result

    @property
    def current(self) -> Behaviour | None:
        return self._last_result
