"""Immutable attention shared by gaze and subjective visual evidence."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from ..balance import BALANCE

AttentionMode = Literal["survey", "cursor", "moving", "object", "unavailable"]
LookSide = Literal[-1, 1]


@dataclass(frozen=True, slots=True)
class ObjectAttention:
    """An eye origin and body width in sensor coordinates; direction is relative."""

    mode: AttentionMode
    direction: tuple[float, float] | None
    origin: tuple[float, float] = (0, 0)
    width: float = 1
    focused_place: bool = False

    def sees_environment(self, x: float, height: float) -> bool:
        """One-width near field, then the forward half of the notice range."""
        if self.mode in ("object", "unavailable"):
            return False
        x, height = (
            (x - self.origin[0]) / self.width,
            (height - self.origin[1]) / self.width,
        )
        distance = math.hypot(x, height)
        if distance <= 1:
            return True
        if distance > BALANCE.number("object_behavior", "notice_widths"):
            return False
        direction = self.direction
        return (
            direction is not None
            and direction != (0, 0)
            and x * direction[0] + height * direction[1] >= 0
        )

    def sees(self, x: float, height: float) -> bool:
        """Include the selected ground place, never surroundings during hand focus."""
        if self.sees_environment(x, height):
            return True
        if not self.focused_place or self.direction is None:
            return False
        x, height = (
            (x - self.origin[0]) / self.width,
            (height - self.origin[1]) / self.width,
        )
        return math.hypot(*self.direction) <= BALANCE.number(
            "object_behavior", "notice_widths"
        ) and math.hypot(
            x - self.direction[0], height - self.direction[1]
        ) <= BALANCE.number("object_behavior", "memory_place_widths")


@dataclass(frozen=True, slots=True)
class KnownPlaceCoverage:
    """A deliberate side check, qualified by the same currently sampled gaze."""

    side: LookSide

    def contains(
        self, x: float, *, attention: ObjectAttention,
        ground_bounds: tuple[float, float],
    ) -> bool:
        return (
            attention.mode == "survey"
            and attention.direction == (self.side, 0)
            and ground_bounds[0] <= x <= ground_bounds[1]
            and (x - attention.origin[0]) * self.side >= 0
        )
