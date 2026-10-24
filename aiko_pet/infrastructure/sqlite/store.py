"""Complete revision-guarded SQLite store; not wired into the desktop yet.

All domain progression remains in PetSessionRestorer and existing owners.
Legacy initialization shares the same transactional writer/publication path.
"""

from __future__ import annotations

import sqlite3
import time
from copy import deepcopy
from pathlib import Path

from ...application.session import LoadedPetData
from ...application.settings import PetSettings
from ...application.social_history import SocialContentHistory
from ...application.storage_contracts import (
    SaveRevision,
    StorageError,
    StorageFailureKind,
)
from ...pet.food_catalog import DEFAULT_CATALOG
from ...pet.mind.adaptive_models import AdaptiveMemory
from ...pet.mind.object_knowledge import ObjectMemorySnapshot
from ...pet.state import PetState
from ...world.contracts import ObjectDefinition, WorldSnapshot
from ..item_assets import load_item_catalog
from ..world_catalog import build_consumable_definitions
from .connection import open_database
from .errors import storage_failures
from .publication import publish_database, temporary_database
from .rows import nonnegative, read_rows
from .session_rows import read_session_rows, write_session_rows


class SqliteStateStore:
    """Own a path, not a second mutable revision, pet or long-lived connection."""

    def __init__(
        self,
        path: Path,
        *,
        definitions: tuple[ObjectDefinition, ...] | None = None,
    ) -> None:
        self.path = path
        self._definitions = definitions

    def _world_definitions(self) -> tuple[ObjectDefinition, ...]:
        return (
            self._definitions
            if self._definitions is not None
            else build_consumable_definitions(DEFAULT_CATALOG, load_item_catalog())
        )

    def _exists(self) -> bool:
        try:
            self.path.stat()
        except FileNotFoundError:
            return False
        return True

    def load_session(self, *, now: float | None = None) -> LoadedPetData:
        with storage_failures(self.path):
            if not self._exists():
                current = nonnegative(
                    time.time() if now is None else now, "fresh UTC time"
                )
                return LoadedPetData(
                    PetState(updated_at=current), PetSettings(), AdaptiveMemory(), False
                )
            with open_database(self.path, transaction="read") as connection:
                loaded = read_session_rows(connection, self._world_definitions())
                connection.commit()
                return loaded

    def save(
        self,
        pet: PetState,
        settings: PetSettings,
        *,
        expected_revision: SaveRevision,
        adaptive: AdaptiveMemory,
        social_history: SocialContentHistory,
        world: WorldSnapshot | None = None,
        world_recovery_x: float = 0,
        object_memory: ObjectMemorySnapshot | None = None,
    ) -> SaveRevision:
        return self._save_snapshot(
            LoadedPetData(pet, settings, adaptive, True, world, object_memory,
                          social_history, expected_revision),
            world_recovery_x=world_recovery_x,
        )

    def initialize_legacy_session(
        self, session: LoadedPetData, *, imported_at: float,
    ) -> SaveRevision:
        """Publish a checked, backed-up import through the existing first writer.

        Revision zero can never update an existing checkpoint. Publication also
        rejects another initializer winning after our existence check.
        """
        with storage_failures(self.path):
            if session.revision != SaveRevision() or not session.restored_from_save:
                raise ValueError("Import requires an unsaved legacy checkpoint")
            stamp = nonnegative(imported_at, "import UTC time")
            return self._save_snapshot(session, world_recovery_x=0, imported_at=stamp)

    def _save_snapshot(
        self, session: LoadedPetData, *, world_recovery_x: float,
        imported_at: float | None = None,
    ) -> SaveRevision:
        with storage_failures(self.path):
            expected_revision = session.revision
            if not isinstance(expected_revision, SaveRevision):
                raise ValueError("Expected revision must use the application contract")
            revision = SaveRevision(expected_revision.value + 1)
            values = session.state.capture_checkpoint()
            saved_settings = deepcopy(session.settings)
            saved_adaptive = deepcopy(session.adaptive_memory)

            def commit_snapshot(
                connection: sqlite3.Connection, *, initial: bool
            ) -> SaveRevision:
                if initial:
                    connection.execute(
                        "INSERT INTO save_state VALUES (1, ?, ?, ?)",
                        (revision.value, values.updated_at, values.lived_seconds),
                    )
                    if imported_at is not None:
                        connection.execute(
                            "INSERT INTO import_provenance VALUES (1, 'json-v1', ?)",
                            (imported_at,),
                        )
                else:
                    changed = connection.execute(
                        "UPDATE save_state SET revision = ?, updated_at = ?, "
                        "lived_seconds = ? "
                        "WHERE id = 1 AND revision = ?",
                        (
                            revision.value,
                            values.updated_at,
                            values.lived_seconds,
                            expected_revision.value,
                        ),
                    ).rowcount
                    if changed != 1:
                        raise StorageError(
                            StorageFailureKind.STALE_REVISION,
                            self.path,
                            "Saved revision no longer matches this session",
                        )
                write_session_rows(
                    connection,
                    values,
                    saved_settings,
                    adaptive=saved_adaptive,
                    social_history=session.social_history,
                    world=session.world,
                    object_memory=session.object_memory,
                    world_recovery_x=world_recovery_x,
                )
                # Validate the complete result before commit or first publication.
                read_session_rows(connection, self._world_definitions())
                if read_rows(connection, "PRAGMA foreign_key_check"):
                    raise ValueError("Snapshot contains invalid owned relationships")
                connection.commit()
                return revision

            if self._exists():
                with open_database(self.path, transaction="write") as connection:
                    return commit_snapshot(connection, initial=False)
            if expected_revision.value != 0:
                raise StorageError(
                    StorageFailureKind.STALE_REVISION,
                    self.path,
                    "The expected saved checkpoint is missing",
                )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_database(self.path) as temporary:
                with open_database(
                    temporary, initialize=True, transaction="write",
                ) as connection:
                    commit_snapshot(connection, initial=True)
                publish_database(temporary, self.path)
            return revision
