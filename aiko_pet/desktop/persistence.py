"""Save already-advanced pet state and manage autosave cadence.

Pet time progression belongs to the application layer; writing a snapshot
never alters needs, daily rhythm, or the unchanged JSON schema.
"""

from __future__ import annotations

import time
from typing import Callable

from ..application.settings import PetSettings
from ..infrastructure.persistence import StateStore
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState
from ..world.contracts import WorldSnapshot

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
        self._world: Callable[[], WorldSnapshot] | None = None
        self._world_x: Callable[[], float] = lambda: 0.0

    def attach_world(
        self, snapshot: Callable[[], WorldSnapshot], recovery_x: Callable[[], float],
    ) -> None:
        self._world, self._world_x = snapshot, recovery_x

    def due(self, now: float) -> bool:
        return now - self.last_saved >= AUTOSAVE_SECONDS

    def save(self) -> OSError | None:
        """Write the current state and update timing even after I/O error."""
        failure: OSError | None = None
        try:
            if self._world is None:
                self._store.save(
                    self._state, self._settings, adaptive=self._adaptive.memory,
                )
            else:
                self._store.save(
                    self._state, self._settings, adaptive=self._adaptive.memory,
                    world=self._world(), world_recovery_x=self._world_x(),
                )
        except OSError as error:
            failure = error
        self.last_saved = self._monotonic()
        return failure
