"""Restore a desktop pet session without coupling application code to disk I/O.

The repository only decodes saved values. This application service applies
bounded elapsed-time simulation for a successfully restored save.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol

from ..adaptive import AdaptiveRoutine
from ..adaptive_models import AdaptiveMemory
from ..domain import PetState
from .settings import PetSettings


@dataclass(frozen=True, slots=True)
class LoadedPetData:
    """Decoded repository data, with explicit provenance for catch-up rules."""

    state: PetState
    settings: PetSettings
    adaptive_memory: AdaptiveMemory
    restored_from_save: bool


class SavedPetReader(Protocol):
    """Read saved values without performing any domain simulation."""

    def load_session(self, *, now: float | None = None) -> LoadedPetData: ...


@dataclass(frozen=True, slots=True)
class RestoredPetSession:
    """References to the mutable objects used for this desktop session."""

    state: PetState
    settings: PetSettings
    adaptive: AdaptiveRoutine


class PetSessionRestorer:
    """Apply original startup catch-up only when a valid save was recovered."""

    def __init__(
        self, reader: SavedPetReader, *,
        wall_time: Callable[[], float] = time.time,
    ) -> None:
        self._reader = reader
        self._wall_time = wall_time

    def restore(self) -> RestoredPetSession:
        now = self._wall_time()
        loaded = self._reader.load_session(now=now)
        if loaded.restored_from_save:
            loaded.state.advance(
                now, auto_routine=loaded.settings.auto_routine,
            )
        return RestoredPetSession(
            state=loaded.state,
            settings=loaded.settings,
            adaptive=AdaptiveRoutine(loaded.adaptive_memory),
        )
