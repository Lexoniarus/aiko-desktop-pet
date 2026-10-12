"""Local, bounded adaptive routine and situational memory for Aiko.

The clock gives Aiko her *own* day. Telemetry describes the effort she
experiences. System uptime alone is never interpreted as time spent working.
Only 168 aggregated hour-of-week buckets and small scalar state are saved;
no keystrokes, process names, window titles, or raw utilization traces.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .routine import TimeContext, context_at

SLOTS = 7 * 24
MAX_OBSERVATION_SECONDS = 30.0
DAILY_DECAY = 0.965  # Long-term half-life ~19 days; no one-off takeover.


def clamp(value: Any, default: float = 0.0, high: float = 100.0) -> float:
    if type(value) not in (float, int):
        return default
    number = float(value)
    if not math.isfinite(number):
        return default
    return min(high, max(0.0, number))


def _hours(raw: Any) -> list[float]:
    if not isinstance(raw, list) or len(raw) != SLOTS:
        return [0.0] * SLOTS
    return [clamp(value, high=500_000.0) for value in raw]


@dataclass(frozen=True)
class Observation:
    """One sampled instant; idle_seconds may be unknown, never guessed."""

    wall_time: float
    effort: float | None
    idle_seconds: float | None
    uptime_hours: float | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.wall_time):
            raise ValueError("wall_time must be finite")
        if self.effort is not None and not 0 <= self.effort <= 1:
            raise ValueError("effort outside 0..1")
        if self.idle_seconds is not None and (
            not math.isfinite(self.idle_seconds) or self.idle_seconds < 0
        ):
            raise ValueError("invalid idle time")


@dataclass
class AdaptiveMemory:
    """Durable aggregates, not a log of the user's actions."""

    hour_seconds: list[float] = field(default_factory=lambda: [0.0] * SLOTS)
    busy_seconds: list[float] = field(default_factory=lambda: [0.0] * SLOTS)
    present_seconds: list[float] = field(default_factory=lambda: [0.0] * SLOTS)
    observed_days: list[float] = field(default_factory=lambda: [0.0] * SLOTS)
    last_slot_key: str = ""
    profile_day: str = ""
    strain: float = 0.0
    settled_work: float = 0.0
    session_seconds: float = 0.0
    rest_seconds: float = 0.0
    last_session_seconds: float = 0.0
    last_work_wall: float = 0.0
    last_contact_wall: float = 0.0
    last_seen_wall: float = 0.0

    @classmethod
    def from_dict(cls, payload: Any) -> AdaptiveMemory:
        if not isinstance(payload, dict):
            return cls()
        last_slot = payload.get("last_slot_key", "")
        day = payload.get("profile_day", "")
        return cls(
            hour_seconds=_hours(payload.get("hour_seconds")),
            busy_seconds=_hours(payload.get("busy_seconds")),
            present_seconds=_hours(payload.get("present_seconds")),
            observed_days=_hours(payload.get("observed_days")),
            last_slot_key=last_slot if isinstance(last_slot, str) and len(last_slot) <= 20 else "",
            profile_day=day if isinstance(day, str) and len(day) == 10 else "",
            strain=clamp(payload.get("strain")),
            settled_work=clamp(payload.get("settled_work"), high=1.0),
            session_seconds=clamp(payload.get("session_seconds"), high=172_800.0),
            rest_seconds=clamp(payload.get("rest_seconds"), high=172_800.0),
            last_session_seconds=clamp(payload.get("last_session_seconds"), high=172_800.0),
            last_work_wall=clamp(payload.get("last_work_wall"), high=4_000_000_000.0),
            last_contact_wall=clamp(payload.get("last_contact_wall"), high=4_000_000_000.0),
            last_seen_wall=clamp(payload.get("last_seen_wall"), high=4_000_000_000.0),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hour_seconds": [round(v, 2) for v in self.hour_seconds],
            "busy_seconds": [round(v, 2) for v in self.busy_seconds],
            "present_seconds": [round(v, 2) for v in self.present_seconds],
            "observed_days": [round(v, 3) for v in self.observed_days],
            "last_slot_key": self.last_slot_key,
            "profile_day": self.profile_day,
            "strain": round(self.strain, 3),
            "settled_work": round(self.settled_work, 4),
            "session_seconds": round(self.session_seconds, 2),
            "rest_seconds": round(self.rest_seconds, 2),
            "last_session_seconds": round(self.last_session_seconds, 2),
            "last_work_wall": round(self.last_work_wall, 2),
            "last_contact_wall": round(self.last_contact_wall, 2),
            "last_seen_wall": round(self.last_seen_wall, 2),
        }


@dataclass(frozen=True)
class Behaviour:
    """Interpretation, not a speech line. Consumers select real sprites."""

    mode: str
    strain: float
    effort: float | None
    expected_effort: float | None
    expectation_confident: bool
    present: bool | None
    uptime_hours: float | None
    prolonged_work_seconds: float
    rest_seconds: float
    can_sleep: bool
    should_wake: bool
    can_nap: bool

    @property
    def focused(self) -> bool:
        return self.mode == "working"

    @property
    def quiet(self) -> bool:
        return self.mode in ("resting", "recovering")


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

    def observe(self, observation: Observation, monotonic: float,
                *, energy: float, sleeping: bool,
                manual_sleep: bool = False, learn: bool = True) -> Behaviour:
        if not math.isfinite(monotonic):
            raise ValueError("monotonic clock must be finite")
        current = observation.wall_time
        context = context_at(current)
        if learn:
            self._age_profile(context.day_key)
        last = self._previous_mono
        if last is None and self.memory.last_seen_wall:
            # Aiko wasn't observing while the application was closed. Don't
            # claim idle time or work then, and don't preserve days-old effort.
            unseen = current - self.memory.last_seen_wall
            if unseen > 1800:
                self.memory.session_seconds = 0.0
                self.memory.rest_seconds = 0.0
                self.memory.settled_work = 0.0
                self.memory.last_session_seconds = 0.0
                self.memory.last_work_wall = 0.0
            if unseen > 6 * 3600:
                self.memory.strain = min(self.memory.strain, 35.0)
        dt = 0.0 if last is None else monotonic - last
        if not 0 <= dt <= 120:
            dt = 0.0  # Resume from suspend, debugging pause, reboot.
        dt = min(MAX_OBSERVATION_SECONDS, dt)
        self._previous_mono = monotonic
        self._previous_wall = current
        self.memory.last_seen_wall = current
        effort = observation.effort
        present = (observation.idle_seconds < 300
                   if observation.idle_seconds is not None else None)

        if effort is not None:
            # 40s smoothing to reject single 6s transient spikes.
            alpha = 1.0 - math.exp(-dt / 40.0)
            if last is None:
                self.memory.settled_work = effort
            else:
                self.memory.settled_work += alpha * (
                    effort - self.memory.settled_work
                )
            self.memory.settled_work = clamp(self.memory.settled_work, high=1.0)
            if dt > 0:
                if effort >= 0.65:
                    self.memory.strain += (effort - 0.45) * dt / 3600 * 55
                else:
                    self.memory.strain -= max(0.15, 0.65 - effort) * dt / 3600 * 38
                self.memory.strain = clamp(self.memory.strain)
                if effort >= 0.65:
                    self.memory.session_seconds = min(
                        172_800, self.memory.session_seconds + dt,
                    )
                    self.memory.last_work_wall = current
                    self.memory.rest_seconds = 0.0
                elif effort < 0.33:
                    if self.memory.session_seconds > 0:
                        self.memory.last_session_seconds = self.memory.session_seconds
                        self.memory.session_seconds = 0.0
                    if present is False:
                        self.memory.rest_seconds = min(
                            172_800, self.memory.rest_seconds + dt,
                        )
                    else:
                        self.memory.rest_seconds = 0.0
                else:
                    self.memory.rest_seconds = 0.0
        # A missing CPU/GPU reading cannot contribute fictitious busy/idle time.
        if learn and dt > 0 and effort is not None:
            slot = self._slot(context)
            self.memory.hour_seconds[slot] += dt
            self.memory.busy_seconds[slot] += dt * effort
            if present is True:
                self.memory.present_seconds[slot] += dt
            key = f"{context.day_key}:{context.local.hour:02d}"
            if key != self.memory.last_slot_key:
                self.memory.observed_days[slot] += 1.0
                self.memory.last_slot_key = key
        expected, confident = self.expected_effort(context) if learn else (None, False)
        current_effort = self.memory.settled_work if effort is not None else None
        # Moderate work should not count as rest. At high current load Aiko is
        # working, even if the user is absent or the local clock says midnight.
        working = effort is not None and (
            effort >= 0.75 or self.memory.settled_work >= 0.59
        )
        if working:
            mode = "working"
        elif (self.memory.last_session_seconds >= 120
              and 0 <= current - self.memory.last_work_wall <= 180):
            mode = "recovering"
        elif self.memory.rest_seconds >= 300:
            mode = "resting"
        elif present is True:
            mode = "present"
        else:
            mode = "wandering"
        # Bedtime is a bias, not a mandatory shutdown. Aiko may also doze after
        # prolonged unattended calm if she is genuinely short on energy.
        late = context.night
        enough_quiet = not working and (
            (effort is None or effort < 0.38) and
            (observation.idle_seconds is None or observation.idle_seconds >= 180)
        )
        can_sleep = ((late and not working and
                      (enough_quiet or energy <= 17)) or
                     (energy <= 23 and self.memory.rest_seconds >= 1800))
        should_wake = (not manual_sleep and sleeping and
                       (working or (not late and present is True)))
        # A learned quiet window makes a daytime nap plausible; low-energy
        # safety fallback also works before weeks of profile observations.
        can_nap = (not late and present is False and not working and
                   self.memory.rest_seconds >= 900 and
                   (energy <= 18 or (energy <= 35 and expected is not None
                                     and expected < 0.32)))
        result = Behaviour(
            mode=mode, strain=self.memory.strain, effort=current_effort,
            expected_effort=expected, expectation_confident=confident,
            present=present,
            uptime_hours=observation.uptime_hours,
            prolonged_work_seconds=self.memory.session_seconds,
            rest_seconds=self.memory.rest_seconds,
            can_sleep=can_sleep, should_wake=should_wake,
            can_nap=can_nap,
        )
        self._last_result = result
        return result

    @property
    def current(self) -> Behaviour | None:
        return self._last_result
