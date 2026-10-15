"""Time-based perception; only confirmed observations enter subjective memory."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE

ConsumableKind = Literal["food", "drink"]


@dataclass(frozen=True, slots=True)
class ObjectCandidate:
    """Sensor input; real identity is private to the recognition policy."""

    token: str
    identity: str
    kind: ConsumableKind
    x: float
    height: float
    resting: bool


@dataclass(frozen=True, slots=True)
class ObjectObservation:
    token: str
    identity: str | None
    kind: ConsumableKind | None
    x: float
    height: float
    resting: bool
    observed_at: float
    examined: bool = False


@dataclass
class _Evidence:
    notice: float = 0.0
    recognize: float = 0.0
    recognizable: bool = False


class ObjectPerception:
    """Accumulate only continuous, attentive observation in active seconds."""

    def __init__(self) -> None:
        self._previous: float | None = None
        self._evidence: dict[str, _Evidence] = {}

    def observe(
        self, candidates: tuple[ObjectCandidate, ...], *, now: float,
        x: float, height: float, width: float, attentive: bool,
    ) -> tuple[ObjectObservation, ...]:
        if not math.isfinite(now) or width <= 0 or not math.isfinite(width):
            raise ValueError("Perception requires finite time and positive width")
        elapsed = 0.0 if self._previous is None else max(0.0, now - self._previous)
        self._previous = now
        evidence: dict[str, _Evidence] = {}
        observations: list[ObjectObservation] = []
        for item in candidates if attentive else ():
            distance = math.hypot(item.x - x, item.height - height) / width
            if distance > BALANCE.number("object_behavior", "notice_widths"):
                continue
            old = self._evidence.get(item.token)
            current = old or _Evidence()
            recognizable = distance <= BALANCE.number(
                "object_behavior", "recognize_widths",
            )
            if old is not None:
                current.notice += elapsed
                if recognizable and current.recognizable:
                    current.recognize += elapsed
                else:
                    current.recognize = 0
            current.recognizable = recognizable
            evidence[item.token] = current
            if current.notice + 1e-9 < BALANCE.number(
                "object_behavior", "notice_seconds",
            ):
                continue
            recognized = current.recognize + 1e-9 >= BALANCE.number(
                "object_behavior", "recognize_seconds",
            )
            observations.append(ObjectObservation(
                item.token, item.identity if recognized else None,
                item.kind if recognized else None, item.x, item.height,
                item.resting, now,
            ))
        self._evidence = evidence
        return tuple(observations)
