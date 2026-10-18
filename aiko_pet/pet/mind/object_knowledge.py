"""Learned facts and portable memory values, separate from sensory evidence."""

from dataclasses import dataclass
from typing import Literal

from .object_perception import ConsumableKind

ObjectDisposition = Literal["deferred", "interrupted"]
# Superseded records are consumed-find witnesses with unresolved associations;
# they are never available stock or visual reunion candidates.
PlaceStatus = Literal["remembered", "missing", "superseded"]


@dataclass(frozen=True, slots=True)
class ObjectKnowledge:
    token: str
    identity: str | None
    kind: ConsumableKind | None
    x: float
    height: float
    resting: bool
    observed_at: float
    assessed: bool = False
    disposition: ObjectDisposition | None = None
    place_status: PlaceStatus = "remembered"
    possible_sources: tuple[str, ...] = ()
    # Acquired only through hand/face identification, never from a remembered place.
    instance_id: str | None = None

    @property
    def recognized(self) -> bool:
        return self.identity is not None and self.kind is not None

    def at_place(self, *, x: float, height: float, resting: bool) -> bool:
        """Compare an observed place exactly; proximity is not object identity."""
        return (self.x, self.height, self.resting) == (x, height, resting)


@dataclass(frozen=True, slots=True)
class SavedObjectKnowledge:
    """Age is active elapsed time, never a process-local or wall-clock stamp."""

    token: str
    identity: str | None
    kind: ConsumableKind | None
    x: float
    height: float
    resting: bool
    age_seconds: float
    assessed: bool
    disposition: ObjectDisposition | None
    place_status: PlaceStatus = "remembered"
    possible_sources: tuple[str, ...] = ()
    instance_id: str | None = None


@dataclass(frozen=True, slots=True)
class ObjectMemorySnapshot:
    entries: tuple[SavedObjectKnowledge, ...] = ()
    next_record_id: int = 1
