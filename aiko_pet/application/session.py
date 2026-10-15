"""Restore a desktop pet session without coupling application code to disk I/O.

The repository only decodes saved values. This service advances closed time
with unknown activity and optional routine self-care before anchoring a session.
"""

from __future__ import annotations

import time
import math
from dataclasses import dataclass
from typing import Callable, Protocol

from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.adaptive_models import AdaptiveMemory
from ..pet.state import PetState
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
    """Restore version-one data and simulate bounded, unobserved closed time."""

    def __init__(
        self,
        reader: SavedPetReader,
        *,
        wall_time: Callable[[], float] = time.time,
    ) -> None:
        self._reader = reader
        self._wall_time = wall_time

    def restore(self) -> RestoredPetSession:
        now = self._wall_time()
        loaded = self._reader.load_session(now=now)
        elapsed = now - loaded.state.updated_at
        if loaded.restored_from_save and math.isfinite(elapsed) and elapsed > 0:
            loaded.state.advance(
                now,
                auto_routine=loaded.settings.auto_routine,
                elapsed_seconds=elapsed,
                self_care=True,
            )
        loaded.state.updated_at = now
        return RestoredPetSession(
            state=loaded.state,
            settings=loaded.settings,
            adaptive=AdaptiveRoutine(loaded.adaptive_memory),
        )
