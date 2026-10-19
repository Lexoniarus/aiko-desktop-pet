"""Adaptive routine orchestrator driven by observed, bounded local telemetry.

Models and persisted memory contracts live in adaptive_models.py; classification
thresholds live in adaptive_policy.py. Consumers import each owning module.
"""

from __future__ import annotations

import math
from datetime import datetime

from ..balance import BALANCE
from ..routine import TimeContext, context_at
from ..sleep import SleepContext, setting
from .adaptive_models import (
    DAILY_DECAY,
    MAX_OBSERVATION_SECONDS,
    SLOTS,
    AdaptiveMemory,
    Behaviour,
    Observation,
    clamp,
)
from .adaptive_policy import determine_activity_mode
from .quiet_rhythm import QuietPhase, QuietWindow


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
        self._input_start = 0.0
        self._input_wall: float | None = None
        self._input_mono: float | None = None
        self._last_input: float | None = None
        self._active_since: float | None = None
        self._last_event_mono: float | None = None
        self._input_events = 0
        self._quiet_since: float | None = None
        self._quiet_learnable = False
        self._sleep_context = SleepContext()

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
                elapsed = (
                    datetime.fromisoformat(today).date()
                    - datetime.fromisoformat(previous).date()
                ).days
        except ValueError:
            elapsed = 0
        if elapsed > 0:
            factor = DAILY_DECAY ** min(
                BALANCE.integer("adaptive_learning", "maximum_decay_days"), elapsed
            )
            for series in (
                self.memory.hour_seconds,
                self.memory.busy_seconds,
                self.memory.present_seconds,
                self.memory.observed_days,
            ):
                for index, amount in enumerate(series):
                    series[index] = round(amount * factor, 4)
        self.memory.profile_day = today

    def expected_effort(self, context: TimeContext) -> tuple[float | None, bool]:
        """Require separate observed days; a 72-hour single run isn't 3 weeks."""
        slot = self._slot(context)
        seconds = self.memory.hour_seconds[slot]
        days = self.memory.observed_days[slot]
        if seconds < BALANCE.integer(
            "adaptive_learning", "minimum_slot_observation_seconds"
        ) or days < BALANCE.number("adaptive_learning", "minimum_profile_days"):
            return None, False
        return self.memory.busy_seconds[slot] / seconds, days >= BALANCE.number(
            "adaptive_learning", "confident_profile_days"
        )

    def note_interaction(self, now_wall: float) -> None:
        if math.isfinite(now_wall) and now_wall > 0:
            self.memory.last_contact_wall = now_wall

    def forget_profile(self) -> None:
        self.memory.quiet_window = QuietWindow()
        self._quiet_since = None
        self._input_start = self._input_wall or 0.0
        for series in (
            self.memory.hour_seconds,
            self.memory.busy_seconds,
            self.memory.present_seconds,
            self.memory.observed_days,
        ):
            series[:] = [0.0] * SLOTS
        self.memory.last_slot_key = ""
        self.memory.profile_day = ""

    def _elapsed_observation_seconds(
        self,
        wall_time: float,
        monotonic: float,
    ) -> tuple[float | None, float]:
        """Reset stale sessions and ignore suspend/debugger time jumps."""
        previous = self._previous_mono
        if previous is None and self.memory.last_seen_wall:
            # Offline time is never interpreted as observed work or idle time.
            unseen = wall_time - self.memory.last_seen_wall
            if unseen > BALANCE.integer(
                "adaptive_learning", "reset_session_after_seconds"
            ):
                self.memory.session_seconds = 0.0
                self.memory.rest_seconds = 0.0
                self.memory.settled_work = 0.0
                self.memory.last_session_seconds = 0.0
                self.memory.last_work_wall = 0.0
            if unseen > BALANCE.integer(
                "adaptive_learning", "relax_strain_after_seconds"
            ):
                self.memory.strain = min(
                    self.memory.strain,
                    BALANCE.number(
                        "adaptive_learning", "maximum_strain_after_long_absence"
                    ),
                )
        elapsed = 0.0 if previous is None else monotonic - previous
        if (
            not 0
            <= elapsed
            <= BALANCE.integer("adaptive_learning", "maximum_observation_gap_seconds")
        ):
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
        alpha = 1.0 - math.exp(
            -elapsed / BALANCE.number("adaptive_learning", "effort_smoothing_seconds")
        )
        if previous is None:
            self.memory.settled_work = effort
        else:
            self.memory.settled_work += alpha * (effort - self.memory.settled_work)
        self.memory.settled_work = clamp(self.memory.settled_work, high=1.0)
        if elapsed <= 0:
            return
        if effort >= BALANCE.number("adaptive_learning", "working_effort_threshold"):
            self.memory.strain += (
                (effort - BALANCE.number("adaptive_learning", "strain_effort_baseline"))
                * elapsed
                / 3600
                * BALANCE.integer("adaptive_learning", "strain_gain_per_hour")
            )
        else:
            self.memory.strain -= (
                max(
                    BALANCE.number("adaptive_learning", "minimum_strain_recovery"),
                    BALANCE.number("adaptive_learning", "strain_recovery_baseline")
                    - effort,
                )
                * elapsed
                / 3600
                * BALANCE.integer("adaptive_learning", "strain_recovery_per_hour")
            )
        self.memory.strain = clamp(self.memory.strain)
        if effort >= BALANCE.number("adaptive_learning", "working_effort_threshold"):
            self.memory.session_seconds = min(
                BALANCE.integer("adaptive_learning", "maximum_episode_seconds"),
                self.memory.session_seconds + elapsed,
            )
            self.memory.last_work_wall = wall_time
            self.memory.rest_seconds = 0.0
        elif effort < BALANCE.number("adaptive_learning", "rest_effort_threshold"):
            if self.memory.session_seconds > 0:
                self.memory.last_session_seconds = self.memory.session_seconds
                self.memory.session_seconds = 0.0
            if present is False:
                self.memory.rest_seconds = min(
                    BALANCE.integer("adaptive_learning", "maximum_episode_seconds"),
                    self.memory.rest_seconds + elapsed,
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
            wall_time,
            monotonic,
        )
        effort = observation.effort
        present = (
            observation.idle_seconds
            < BALANCE.integer("adaptive_learning", "present_idle_seconds")
            if observation.idle_seconds is not None
            else None
        )
        self._update_workload_memory(
            effort,
            elapsed=elapsed,
            previous=previous,
            wall_time=wall_time,
            present=present,
        )
        self._record_hourly_exposure(
            context,
            elapsed=elapsed,
            effort=effort,
            present=present,
            learn=learn,
        )
        expected, confident = self.expected_effort(context) if learn else (None, False)
        mode = determine_activity_mode(
            effort=effort,
            settled_work=self.memory.settled_work,
            last_session_seconds=self.memory.last_session_seconds,
            last_work_wall=self.memory.last_work_wall,
            rest_seconds=self.memory.rest_seconds,
            present=present,
            wall_time=wall_time,
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
        )
        self._last_result = result
        return result

    def observe_input(
        self,
        *,
        wall: float,
        monotonic: float,
        idle_seconds: float | None,
        learn: bool = True,
        unavailable_seconds: float = 0.0,
    ) -> SleepContext:
        """Observe changes in anonymous OS last-input time, not keys or load."""
        previous = self._input_mono
        gap = 0.0 if previous is None else monotonic - previous
        previous_wall = self._input_wall
        self._input_mono, self._input_wall = monotonic, wall
        valid = (
            idle_seconds is not None
            and math.isfinite(idle_seconds)
            and idle_seconds >= 0
            and math.isfinite(wall)
            and math.isfinite(monotonic)
        )
        if (
            previous is None
            or gap < 0
            or gap > setting("sample_gap_seconds")
            or previous_wall is None
            or abs((wall - previous_wall) - gap) > 5
        ):
            self._active_since = self._last_event_mono = None
            self._input_events = 0
            self._last_input = None
            self._input_start = wall - max(0.0, unavailable_seconds)
            # Only explicitly measured suspension may bridge an observation gap.
            can_bridge = (previous_wall is not None
                          and abs((wall - previous_wall) - gap) <= 5
                          and unavailable_seconds
                          >= gap - setting("sample_gap_seconds"))
            bridge_existing = can_bridge and self._quiet_since is not None
            self._quiet_since = (
                self._quiet_since if bridge_existing
                else wall - unavailable_seconds if unavailable_seconds > 0 else None
            )
            self._quiet_learnable = (self._quiet_learnable and learn
                                     if bridge_existing else learn)
        if not learn:
            self._quiet_learnable = False
        if not valid:
            self._quiet_since = None
            self._sleep_context = self.sleep_context()
            return self._sleep_context
        assert idle_seconds is not None
        event_wall = wall - idle_seconds
        event = (self._last_input is not None
                 and event_wall > self._last_input + 0.05
                 and idle_seconds <= max(0, gap) + .05)
        self._last_input = event_wall
        if event:
            if (
                self._last_event_mono is None
                or monotonic - self._last_event_mono > setting("input_gap_seconds")
            ):
                self._active_since, self._input_events = monotonic, 0
            self._input_events = min(
                int(setting("minimum_input_events")), self._input_events + 1
            )
            self._last_event_mono = monotonic
        active = (
            monotonic - self._active_since
            if self._active_since is not None
            and self._last_event_mono is not None
            and monotonic - self._last_event_mono <= setting("input_gap_seconds")
            and self._input_events >= setting("minimum_input_events")
            else 0.0
        )
        if self._quiet_since is None and idle_seconds >= setting("quiet_seconds"):
            # Never backfill quiet time before this process actually observed it.
            self._quiet_since = max(event_wall, self._input_start)
            self._quiet_learnable = learn
        if self._quiet_since is not None and active >= setting("return_seconds"):
            finish = wall - active
            if (
                learn and self._quiet_learnable
                and setting("minimum_phase_seconds")
                <= finish - self._quiet_since
                <= setting("maximum_phase_seconds")
            ):
                start_local = datetime.fromtimestamp(self._quiet_since)
                end_local = datetime.fromtimestamp(finish)
                self.memory.quiet_window = self.memory.quiet_window.record(
                    QuietPhase(
                        start_local.date().isoformat(),
                        start_local.hour * 60 + start_local.minute,
                        end_local.hour * 60 + end_local.minute,
                    )
                )
            self._quiet_since = None
        # A jitter does not cancel an established quiet interval. Until a repeated
        # return is recognized, ordinary sleep remains possible during that phase.
        quiet_idle = idle_seconds
        if self._quiet_since is not None and self._input_events < setting(
            "minimum_input_events"
        ):
            quiet_idle = max(idle_seconds, wall - self._quiet_since)
        window = self.memory.quiet_window
        self._sleep_context = SleepContext(
            window.start, window.end, quiet_idle, active, observed=True
        )
        return self._sleep_context

    def sleep_context(self, *, observed: bool = False) -> SleepContext:
        window = self.memory.quiet_window
        if observed:
            from dataclasses import replace

            return replace(
                self._sleep_context, start_minute=window.start, end_minute=window.end
            )
        return SleepContext(window.start, window.end)

    @property
    def current(self) -> Behaviour | None:
        return self._last_result
