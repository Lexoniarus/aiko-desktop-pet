"""Small anonymous quiet-window values and recurrence policy, without scores."""

from __future__ import annotations

from dataclasses import dataclass, replace
from statistics import median
from typing import Any

from ..sleep import setting


def distance(a: float, b: float) -> float:
    return (a - b + 720) % 1440 - 720


@dataclass(frozen=True, slots=True)
class QuietPhase:
    day: str
    start: float
    end: float


@dataclass(frozen=True, slots=True)
class QuietWindow:
    start: float = setting("default_start_minute")
    end: float = setting("default_end_minute")
    phases: tuple[QuietPhase, ...] = ()
    adjusted_day: str = ""

    @property
    def recurring(self) -> int:
        return max(
            (
                sum(
                    abs(distance(p.start, anchor.start))
                    <= setting("phase_similarity_minutes")
                    and abs(distance(p.end, anchor.end))
                    <= setting("phase_similarity_minutes")
                    for p in self.phases
                )
                for anchor in self.phases
            ),
            default=0,
        )

    def record(self, phase: QuietPhase) -> QuietWindow:
        if any(p.day == phase.day for p in self.phases):
            return self
        phases = (*self.phases, phase)[-int(setting("learned_phases")) :]
        # Largest similar cluster; ties prefer the established window.
        groups = [
            tuple(
                p
                for p in phases
                if abs(distance(p.start, anchor.start))
                <= setting("phase_similarity_minutes")
                and abs(distance(p.end, anchor.end))
                <= setting("phase_similarity_minutes")
            )
            for anchor in phases
        ]
        group = max(
            groups, key=lambda g: (len(g), -abs(distance(g[0].start, self.start)))
        )
        updated = replace(self, phases=phases)
        if len(group) < setting("tendency_phases") or self.adjusted_day == phase.day:
            return updated
        limit = setting("maximum_daily_shift_minutes")

        starts = [distance(p.start, self.start) for p in group]
        duration = (self.end - self.start) % 1440
        ends = [
            offset + (p.end - p.start) % 1440 - duration
            for p, offset in zip(group, starts)
        ]

        def move(current: float, offsets: list[float]) -> float:
            delta = median(offsets)
            return (current + max(-limit, min(limit, delta))) % 1440

        # Unwrap both endpoints around the same phase start. Independent shortest
        # paths could otherwise collapse an almost opposite daytime window.
        return replace(
            updated,
            start=move(self.start, starts),
            end=move(self.end, ends),
            adjusted_day=phase.day,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "start": self.start,
            "end": self.end,
            "adjusted_day": self.adjusted_day,
            "phases": [
                {"day": p.day, "start": p.start, "end": p.end} for p in self.phases
            ],
        }

    @classmethod
    def from_dict(cls, raw: Any) -> QuietWindow:
        import math
        from datetime import date

        if (
            not isinstance(raw, dict)
            or type(raw.get("version")) is not int
            or raw["version"] != 1
            or set(raw) != {"version", "start", "end", "phases", "adjusted_day"}
        ):
            raise ValueError("Unsupported quiet window")

        def minute(value: Any) -> float:
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0 <= value < 1440
            ):
                raise ValueError("Invalid quiet minute")
            return float(value)

        def day(value: Any, *, optional: bool = False) -> str:
            if optional and value == "":
                return ""
            if (
                not isinstance(value, str)
                or date.fromisoformat(value).isoformat() != value
            ):
                raise ValueError("Invalid quiet day")
            return value

        phases = raw.get("phases")
        if not isinstance(phases, list) or len(phases) > setting("learned_phases"):
            raise ValueError("Invalid quiet phases")
        if any(
            not isinstance(p, dict) or set(p) != {"day", "start", "end"} for p in phases
        ):
            raise ValueError("Invalid quiet phase fields")
        entries = tuple(
            QuietPhase(day(p["day"]), minute(p["start"]), minute(p["end"]))
            for p in phases
            if isinstance(p, dict)
        )
        if len(entries) != len(phases) or len({p.day for p in entries}) != len(entries):
            raise ValueError("Invalid quiet phase dates")
        minimum = setting("minimum_phase_seconds") / 60
        maximum = setting("maximum_phase_seconds") / 60
        if any(not minimum <= (p.end - p.start) % 1440 <= maximum for p in entries):
            raise ValueError("Invalid observed quiet duration")
        start, end = minute(raw.get("start")), minute(raw.get("end"))
        if not minimum <= (end - start) % 1440 <= maximum:
            raise ValueError("Invalid quiet duration")
        return cls(start, end, entries, day(raw.get("adjusted_day", ""), optional=True))
