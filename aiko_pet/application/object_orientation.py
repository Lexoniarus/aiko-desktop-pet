"""Pure progress for one deliberate left/right check of learned places."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from ..pet.mind.object_attention import KnownPlaceCoverage, LookSide, ObjectAttention
from ..pet.mind.object_knowledge import ObjectKnowledge


@dataclass(frozen=True, slots=True)
class OrientationProgress:
    """One transient value; the behavior coordinator owns its replacement."""

    side: LookSide | None = -1
    since: float | None = None
    last: float | None = None

    @property
    def complete(self) -> bool:
        return self.side is None

    @property
    def coverage(self) -> KnownPlaceCoverage | None:
        return KnownPlaceCoverage(self.side) if self.side is not None else None

    def advance(
        self, *, now: float, attention: ObjectAttention,
        known: tuple[ObjectKnowledge, ...], ground_bounds: tuple[float, float],
        duration: float, maximum_gap: float,
    ) -> OrientationProgress:
        if not all(math.isfinite(value) for value in (now, duration, maximum_gap)):
            raise ValueError("Orientation requires finite time and durations")
        if duration <= 0 or maximum_gap <= 0:
            raise ValueError("Orientation durations must be positive")
        if self.complete:
            return self
        if not any(item.recognized and item.resting
                   and item.place_status == "remembered"
                   and ground_bounds[0] <= item.x <= ground_bounds[1]
                   for item in known):
            return OrientationProgress(side=None)
        if attention.mode in ("object", "unavailable"):
            return OrientationProgress()
        if attention.mode != "survey" or attention.direction != (self.side, 0):
            return replace(self, since=None, last=None)
        if (self.last is None or self.since is None
                or not 0 <= now - self.last <= maximum_gap):
            return replace(self, since=now, last=now)
        if now - self.since + 1e-9 < duration:
            return replace(self, last=now)
        return OrientationProgress(side=1 if self.side == -1 else None)
