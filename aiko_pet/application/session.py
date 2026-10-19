"""Restore a desktop pet session without coupling application code to disk I/O.

The repository only decodes saved values. This service advances closed time
with unknown activity before anchoring a session; it never generates resources.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Protocol

from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.adaptive_models import AdaptiveMemory
from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..pet.state import PetState
from ..world.contracts import WorldSnapshot
from .active_time import ActiveSessionClock
from .settings import PetSettings


@dataclass(frozen=True, slots=True)
class WorldSessionSnapshot:
    """Capture the paired physical/cognitive owners on the application thread."""

    world: WorldSnapshot
    object_memory: ObjectMemorySnapshot
    recovery_x: float


@dataclass(frozen=True, slots=True)
class LoadedPetData:
    """Decoded repository data, with explicit provenance for catch-up rules."""

    state: PetState
    settings: PetSettings
    adaptive_memory: AdaptiveMemory
    restored_from_save: bool
    world: WorldSnapshot | None = None
    object_memory: ObjectMemorySnapshot | None = None


class SavedPetReader(Protocol):
    """Read saved values without performing any domain simulation."""

    def load_session(self, *, now: float | None = None) -> LoadedPetData: ...


@dataclass(frozen=True, slots=True)
class RestoredPetSession:
    """References to the mutable objects used for this desktop session."""

    state: PetState
    settings: PetSettings
    adaptive: AdaptiveRoutine
    world: WorldSnapshot | None = None
    object_memory: ObjectMemorySnapshot | None = None


class PetSessionRestorer:
    """Restore version-one data and advance all unobserved closed time once."""

    def __init__(
        self,
        reader: SavedPetReader,
        *,
        wall_time: Callable[[], float] = time.time,
        clock: ActiveSessionClock | None = None,
    ) -> None:
        self._reader = reader
        self._wall_time = wall_time
        self._clock = clock

    def restore(self) -> RestoredPetSession:
        now = self._wall_time()
        if self._clock is not None:
            # Align the live anchor with the closed-time endpoint before I/O
            # and catch-up work, so initialization itself is not lost/replayed.
            self._clock.consume(wall_time=now)
        loaded = self._reader.load_session(now=now)
        elapsed = now - loaded.state.updated_at
        if loaded.restored_from_save and math.isfinite(elapsed) and elapsed > 0:
            loaded.state.advance(
                now,
                auto_routine=loaded.settings.auto_routine,
                elapsed_seconds=elapsed,
            )
        loaded.state.anchor_live_session(now)
        return RestoredPetSession(
            state=loaded.state,
            settings=loaded.settings,
            adaptive=AdaptiveRoutine(loaded.adaptive_memory),
            world=loaded.world,
            object_memory=loaded.object_memory,
        )
