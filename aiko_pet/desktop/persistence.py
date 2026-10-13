"""Save already-advanced pet state and manage autosave cadence.

Pet time progression belongs to the application layer; writing a snapshot
never alters needs, daily rhythm, or the unchanged JSON schema.
"""

from __future__ import annotations

import time
from typing import Callable

from ..adaptive import AdaptiveRoutine
from ..domain import PetState
from ..application.settings import PetSettings
from ..storage import StateStore

AUTOSAVE_SECONDS = 55


class DesktopPersistence:
    """Persist the supplied state and track the next due save time."""

    def __init__(
        self,
        store: StateStore, state: PetState, settings: PetSettings,
        adaptive: AdaptiveRoutine, *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._store = store
        self._state = state
        self._settings = settings
        self._adaptive = adaptive
        self._monotonic = monotonic
        self.last_saved = monotonic()

    def due(self, now: float) -> bool:
        return now - self.last_saved >= AUTOSAVE_SECONDS

    def save(self) -> OSError | None:
        """Write the current state and update timing even after I/O error."""
        failure: OSError | None = None
        try:
            self._store.save(
                self._state, self._settings, adaptive=self._adaptive.memory,
            )
        except OSError as error:
            failure = error
        self.last_saved = self._monotonic()
        return failure
