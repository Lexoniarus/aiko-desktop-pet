"""Save already-advanced pet state and manage autosave cadence.

Pet time progression belongs to the application layer; writing a snapshot
never alters needs, daily rhythm, or the version-one local save format.
"""

from __future__ import annotations

import time
from typing import Callable

from ..application.session import WorldSessionSnapshot
from ..application.settings import PetSettings
from ..application.social_history import SocialContentHistory
from ..infrastructure.persistence import StateStore
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState

AUTOSAVE_SECONDS = 55


class DesktopPersistence:
    """Persist the supplied state and track the next due save time."""

    def __init__(
        self,
        store: StateStore, state: PetState, settings: PetSettings,
        adaptive: AdaptiveRoutine, *,
        monotonic: Callable[[], float] = time.monotonic,
        social_history: Callable[[], SocialContentHistory] = SocialContentHistory,
    ) -> None:
        self._store = store
        self._state = state
        self._settings = settings
        self._adaptive = adaptive
        self._monotonic = monotonic
        self._social_history = social_history
        self.last_saved = monotonic()
        self._world: Callable[[], WorldSessionSnapshot] | None = None

    def attach_world(
        self, snapshot: Callable[[], WorldSessionSnapshot],
    ) -> None:
        self._world = snapshot

    def due(self, now: float) -> bool:
        return now - self.last_saved >= AUTOSAVE_SECONDS

    def save(self) -> OSError | None:
        """Write the current state and update timing even after I/O error."""
        failure: OSError | None = None
        try:
            world = self._world() if self._world is not None else None
            self._store.save(
                self._state, self._settings, adaptive=self._adaptive.memory,
                social_history=self._social_history(),
                world=world.world if world is not None else None,
                world_recovery_x=world.recovery_x if world is not None else 0,
                object_memory=world.object_memory if world is not None else None,
            )
        except OSError as error:
            failure = error
        self.last_saved = self._monotonic()
        return failure
