"""Time-based perception; only confirmed observations enter subjective memory."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE

ConsumableKind = Literal["food", "drink"]


@dataclass(frozen=True, slots=True)
class ItemPresentation:
    """One player gesture, positioned relative to the face in sprite widths."""

    gesture_id: str
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class ObjectCandidate:
    """Sensor input; real identity is private to the recognition policy."""

    token: str
    identity: str
    kind: ConsumableKind
    x: float
    height: float
    resting: bool
    inspecting: bool = False
    presentation: ItemPresentation | None = None


@dataclass(frozen=True, slots=True)
class ObjectObservation:
    token: str
    identity: str | None
    kind: ConsumableKind | None
    x: float
    height: float
    resting: bool
    observed_at: float
    presented: bool = False


@dataclass
class _Evidence:
    notice: float = 0.0
    recognize: float = 0.0
    recognizable: bool = False
    gesture_id: str | None = None
    presentation_anchor: tuple[float, float] | None = None
    presentation_seconds: float = 0.0
    presented: bool = False

    def present(self, pose: ItemPresentation | None, elapsed: float) -> None:
        if pose is None or pose.gesture_id != self.gesture_id:
            self.gesture_id = pose.gesture_id if pose is not None else None
            self.presentation_anchor = None
            self.presentation_seconds = 0
            self.presented = False
        if pose is None or self.presented:
            return
        inside = (abs(pose.x) <= BALANCE.number(
            "object_behavior", "presentation_horizontal_widths",
        ) and abs(pose.y) <= BALANCE.number(
            "object_behavior", "presentation_vertical_widths",
        ))
        if not inside:
            self.presentation_anchor = None
            self.presentation_seconds = 0
            return
        if self.presentation_anchor is None or math.hypot(
            pose.x - self.presentation_anchor[0], pose.y - self.presentation_anchor[1],
        ) > BALANCE.number("object_behavior", "presentation_jitter_widths"):
            self.presentation_anchor = pose.x, pose.y
            self.presentation_seconds = 0
        else:
            self.presentation_seconds += elapsed
        self.presented = self.presentation_seconds + 1e-9 >= BALANCE.number(
            "object_behavior", "presentation_seconds",
        )


class ObjectPerception:
    """Accumulate only continuous, attentive observation in active seconds."""

    def __init__(self) -> None:
        self._previous: float | None = None
        self._evidence: dict[str, _Evidence] = {}
        self._attention_started: float | None = None

    def attentive_seconds(self, now: float) -> float:
        return (max(0.0, now - self._attention_started)
                if self._attention_started is not None else 0.0)

    def observe(
        self, candidates: tuple[ObjectCandidate, ...], *, now: float,
        x: float, height: float, width: float, attentive: bool,
        following: str | None = None,
    ) -> tuple[ObjectObservation, ...]:
        if not math.isfinite(now) or width <= 0 or not math.isfinite(width):
            raise ValueError("Perception requires finite time and positive width")
        elapsed = 0.0 if self._previous is None else max(0.0, now - self._previous)
        self._previous = now
        if not attentive:
            self._attention_started = None
        elif self._attention_started is None:
            self._attention_started = now
        evidence: dict[str, _Evidence] = {}
        observations: list[ObjectObservation] = []
        for item in candidates if attentive else ():
            distance = math.hypot(item.x - x, item.height - height) / width
            if (item.token != following
                    and distance > BALANCE.number("object_behavior", "notice_widths")):
                continue
            old = self._evidence.get(item.token)
            current = old or _Evidence()
            recognizable = item.inspecting
            current.present(item.presentation, elapsed if old is not None else 0)
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
            recognized = current.presented or recognizable and (
                current.recognize + 1e-9 >= BALANCE.number(
                    "object_behavior", "recognize_seconds",
                )
            )
            observations.append(ObjectObservation(
                item.token, item.identity if recognized else None,
                item.kind if recognized else None, item.x, item.height,
                item.resting, now, current.presented,
            ))
        self._evidence = evidence
        return tuple(observations)
