"""Typed adaptive observation and persisted memory models.

Only aggregated hour-of-week counters and bounded numeric values are saved.
No raw utilization samples, window titles or user activity logs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .adaptive_policy import ActivityMode

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
            last_slot_key=(
                last_slot if isinstance(last_slot, str) and len(last_slot) <= 20
                else ""
            ),
            profile_day=day if isinstance(day, str) and len(day) == 10 else "",
            strain=clamp(payload.get("strain")),
            settled_work=clamp(payload.get("settled_work"), high=1.0),
            session_seconds=clamp(payload.get("session_seconds"), high=172_800.0),
            rest_seconds=clamp(payload.get("rest_seconds"), high=172_800.0),
            last_session_seconds=clamp(
                payload.get("last_session_seconds"), high=172_800.0,
            ),
            last_work_wall=clamp(payload.get("last_work_wall"), high=4_000_000_000.0),
            last_contact_wall=clamp(
                payload.get("last_contact_wall"), high=4_000_000_000.0,
            ),
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

    mode: ActivityMode
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


