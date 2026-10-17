"""Local negative sensory evidence; missing World handles prove nothing."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..balance import BALANCE
from .object_knowledge import ObjectKnowledge
from .object_perception import ObjectCandidate


@dataclass
class _EmptyPlace:
    x: float
    height: float
    since: float
    last: float
    confirmed: bool = False


class ObjectAbsencePerception:
    """Require continuous local coverage, including pending positive evidence."""

    def __init__(self) -> None:
        self._places: dict[str, _EmptyPlace] = {}

    @property
    def checking(self) -> bool:
        return any(not place.confirmed for place in self._places.values())

    def observe(
        self, known: tuple[ObjectKnowledge, ...],
        occupants: tuple[ObjectCandidate, ...],
        *, now: float, x: float, height: float, width: float, attentive: bool,
        ground_bounds: tuple[float, float], focused: str | None = None,
    ) -> tuple[str, ...]:
        if not math.isfinite(now) or not math.isfinite(width) or width <= 0:
            raise ValueError("Absence perception requires finite time and width")
        reach = width * BALANCE.number("object_behavior", "memory_place_widths")
        radius = width * BALANCE.number("object_behavior", "notice_widths")
        gap = BALANCE.number("object_behavior", "tracking_gap_seconds")
        duration = BALANCE.number("object_behavior", "absence_seconds")
        places: dict[str, _EmptyPlace] = {}
        confirmed = []
        for item in known if attentive else ():
            if (not item.resting or item.place_status != "remembered"
                    or focused is not None and item.token != focused
                    or not ground_bounds[0] <= item.x <= ground_bounds[1]
                    or math.hypot(item.x - x, item.height - height) > radius
                    or any(math.hypot(candidate.x - item.x,
                                      candidate.height - item.height) <= reach
                           for candidate in occupants)):
                continue
            previous = self._places.get(item.token)
            if (previous is None or not 0 <= now - previous.last <= gap
                    or (previous.x, previous.height) != (item.x, item.height)):
                previous = _EmptyPlace(item.x, item.height, now, now)
            previous.last = now
            if not previous.confirmed and now - previous.since + 1e-9 >= duration:
                previous.confirmed = True
                confirmed.append(item.token)
            places[item.token] = previous
        self._places = places
        return tuple(confirmed)
