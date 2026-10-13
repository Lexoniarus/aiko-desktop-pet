"""State serialization and timed autosaves independently of Tkinter.

The desktop UI decides only how to display returned disk-write failures.
The normal domain advance and unchanged JSON schema stay in this service.
"""

from __future__ import annotations

import time
from typing import Callable, Protocol

from ..adaptive import AdaptiveRoutine
from ..domain import PetState
from ..storage import PetSettings, StateStore

AUTOSAVE_SECONDS = 55


class SaveReadings(Protocol):
    def _allow_bedtime(self) -> bool | None: ...

    def _allow_nap(self) -> bool: ...

    def _interrupt_nap(self) -> bool: ...

    def _live_effort(self) -> float | None: ...


class DesktopPersistence:
    """Catch up the pet, write its existing save, and track the next due time."""

    def __init__(
        self,
        store: StateStore, state: PetState, settings: PetSettings,
        adaptive: AdaptiveRoutine, readings: SaveReadings, *,
        monotonic: Callable[[], float] = time.monotonic,
        wall_time: Callable[[], float] = time.time,
    ) -> None:
        self._store = store
        self._state = state
        self._settings = settings
        self._adaptive = adaptive
        self._readings = readings
        self._monotonic = monotonic
        self._wall_time = wall_time
        self.last_saved = monotonic()

    def due(self, now: float) -> bool:
        return now - self.last_saved >= AUTOSAVE_SECONDS

    def save(self) -> OSError | None:
        """Preserve old advancement and update the time even after I/O error."""
        self._state.advance(
            self._wall_time(),
            auto_routine=self._settings.auto_routine,
            allow_bedtime=self._readings._allow_bedtime(),
            allow_nap=self._readings._allow_nap(),
            interrupt_nap=self._readings._interrupt_nap(),
            effort=self._readings._live_effort(),
        )
        failure: OSError | None = None
        try:
            self._store.save(
                self._state, self._settings, adaptive=self._adaptive.memory,
            )
        except OSError as error:
            failure = error
        self.last_saved = self._monotonic()
        return failure
