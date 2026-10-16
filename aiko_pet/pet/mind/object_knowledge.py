"""Learned facts and portable memory values, separate from sensory evidence."""

from dataclasses import dataclass
from typing import Literal

from .object_perception import ConsumableKind

ObjectDisposition = Literal["deferred", "interrupted"]
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

    @property
    def recognized(self) -> bool:
        return self.identity is not None and self.kind is not None


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


@dataclass(frozen=True, slots=True)
class ObjectMemorySnapshot:
    entries: tuple[SavedObjectKnowledge, ...] = ()
