"""Follow spatial sightings; opaque World handles never prove recognition."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from ..pet.mind.object_perception import ObjectCandidate


@dataclass(frozen=True, slots=True)
class _Track:
    candidate: ObjectCandidate
    observed_at: float


class ObjectTracker:
    """Own session-local sighting handles and current execution bindings.

    Call with only currently visible candidates. Mutual unique nearest matches
    preserve continuity; gaps, implausible jumps and ties start fresh sightings.
    Catalog IDs are carried to the recognizer but never used for association.
    """

    def __init__(self, *, maximum_gap: float) -> None:
        if not math.isfinite(maximum_gap) or maximum_gap <= 0:
            raise ValueError("Tracking gap must be finite and positive")
        self._maximum_gap = maximum_gap
        self._tracks: dict[str, _Track] = {}
        self._bindings: dict[str, str] = {}
        self._serial = 0

    def resolve(self, sighting: str) -> str | None:
        return self._bindings.get(sighting)

    def update(
        self, candidates: tuple[ObjectCandidate, ...], *,
        now: float, maximum_distance: float,
    ) -> tuple[ObjectCandidate, ...]:
        if (not math.isfinite(now) or not math.isfinite(maximum_distance)
                or maximum_distance <= 0):
            raise ValueError("Invalid tracking time/distance")
        previous = {
            token: track for token, track in self._tracks.items()
            if 0 <= now - track.observed_at <= self._maximum_gap + 1e-9
        }
        distances = {
            (index, token): math.hypot(
                item.x - track.candidate.x, item.height - track.candidate.height,
            )
            for index, item in enumerate(candidates)
            for token, track in previous.items()
        }
        nearest: dict[int, str] = {}
        for index in range(len(candidates)):
            options = sorted((distance, token) for (number, token), distance
                             in distances.items() if number == index
                             and distance <= maximum_distance)
            if options and (len(options) == 1 or options[0][0] < options[1][0]):
                nearest[index] = options[0][1]
        result: list[ObjectCandidate] = []
        tracks: dict[str, _Track] = {}
        bindings: dict[str, str] = {}
        for index, item in enumerate(candidates):
            token = nearest.get(index)
            if token is not None:
                competitors = sorted((distance, number) for (number, old), distance
                                     in distances.items() if old == token)
                if (competitors[0][1] != index or len(competitors) > 1
                        and competitors[0][0] == competitors[1][0]):
                    token = None
            if token is None:
                self._serial += 1
                token = f"sighting_{self._serial}"
            tracked = replace(item, token=token)
            tracks[token] = _Track(tracked, now)
            bindings[token] = item.token
            result.append(tracked)
        self._tracks, self._bindings = tracks, bindings
        return tuple(result)
