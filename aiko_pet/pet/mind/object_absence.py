"""Local negative sensory evidence; missing World handles prove nothing."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from ..balance import BALANCE
from .object_attention import ObjectAttention
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
        *, now: float, attention: ObjectAttention,
        ground_bounds: tuple[float, float],
        identified: Mapping[str, ObjectKnowledge] | None = None,
    ) -> tuple[str, ...]:
        width = attention.width
        if not math.isfinite(now) or not math.isfinite(width) or width <= 0:
            raise ValueError("Absence perception requires finite time and width")
        reach = width * BALANCE.number("object_behavior", "memory_place_widths")
        gap = BALANCE.number("object_behavior", "tracking_gap_seconds")
        duration = BALANCE.number("object_behavior", "absence_seconds")
        places: dict[str, _EmptyPlace] = {}
        confirmed = []
        for item in known:
            if (not item.resting or item.place_status != "remembered"
                    or not ground_bounds[0] <= item.x <= ground_bounds[1]
                    or not attention.sees(item.x, item.height)
                    or any(math.hypot(candidate.x - item.x,
                                      candidate.height - item.height) <= reach
                           and self._could_be(item, candidate, identified)
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

    @staticmethod
    def _could_be(
        remembered: ObjectKnowledge, candidate: ObjectCandidate,
        identified: Mapping[str, ObjectKnowledge] | None,
    ) -> bool:
        occupant = identified.get(candidate.token) if identified is not None else None
        if occupant is None:
            return True  # Pending/unknown occupancy first needs investigation.
        return (occupant.token == remembered.token
                or remembered.instance_id is not None
                and occupant.instance_id == remembered.instance_id
                or remembered.instance_id is None
                and (remembered.identity, remembered.kind)
                == (occupant.identity, occupant.kind))
