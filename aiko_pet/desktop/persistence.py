"""Save already-advanced pet state and manage autosave cadence.

Pet time progression belongs to the application layer; writing a snapshot
never alters needs or daily rhythm. The last committed revision changes only
after a successful complete SQLite write.
"""

from __future__ import annotations

import time
from typing import Callable

from ..application.session import SavedPetWriter, WorldSessionSnapshot
from ..application.settings import PetSettings
from ..application.social_history import SocialContentHistory
from ..application.storage_contracts import SaveRevision, StorageError
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState

AUTOSAVE_SECONDS = 55


class DesktopPersistence:
    """Persist the supplied state and track the next due save time."""

    def __init__(
        self,
        store: SavedPetWriter, state: PetState, settings: PetSettings,
        adaptive: AdaptiveRoutine, *,
        revision: SaveRevision = SaveRevision(),
        monotonic: Callable[[], float] = time.monotonic,
        social_history: Callable[[], SocialContentHistory] = SocialContentHistory,
    ) -> None:
        self._store = store
        self._state = state
        self._settings = settings
        self._adaptive = adaptive
        self._monotonic = monotonic
        self._social_history = social_history
        self.revision = revision
        self.last_saved = monotonic()
        self._last_attempt = self.last_saved
        self._world: Callable[[], WorldSessionSnapshot] | None = None

    def attach_world(
        self, snapshot: Callable[[], WorldSessionSnapshot],
    ) -> None:
        self._world = snapshot

    def due(self, now: float) -> bool:
        return now - self._last_attempt >= AUTOSAVE_SECONDS

    def save(self) -> StorageError | None:
        """Keep the last checkpoint on failure; pace retries without replaying care."""
        failure: StorageError | None = None
        try:
            world = self._world() if self._world is not None else None
            revision = self._store.save(
                self._state, self._settings, expected_revision=self.revision,
                adaptive=self._adaptive.memory,
                social_history=self._social_history(),
                world=world.world if world is not None else None,
                world_recovery_x=world.recovery_x if world is not None else 0,
                object_memory=world.object_memory if world is not None else None,
            )
        except StorageError as error:
            failure = error
        else:
            self.revision = revision
            self.last_saved = self._monotonic()
        self._last_attempt = self._monotonic()
        return failure
