"""Complete revision-guarded SQLite store; not wired into the desktop yet.

All domain progression remains in PetSessionRestorer and existing owners. A
path is explicit until the planned import/bootstrap and runtime cutover slices.
"""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
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
from .errors import translate_storage_error
from .publication import publish_database, temporary_database
from .rows import nonnegative, read_rows
from .session_rows import read_session_rows, write_session_rows


@contextmanager
def _storage_failures(path: Path) -> Iterator[None]:
    try:
        yield
    except StorageError as error:
        if error.path == path:
            raise
        raise StorageError(error.kind, path, error.message) from error
    except (sqlite3.Error, OSError) as error:
        raise translate_storage_error(error, path) from error
    except (ValueError, TypeError, OverflowError, KeyError) as error:
        raise StorageError(
            StorageFailureKind.INVALID_DATA, path, "Invalid complete save snapshot"
        ) from error


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
        with _storage_failures(self.path):
            if not self._exists():
                current = nonnegative(
                    time.time() if now is None else now, "fresh UTC time"
                )
                return LoadedPetData(
                    PetState(updated_at=current), PetSettings(), AdaptiveMemory(), False
                )
            with open_database(self.path) as connection:
                connection.execute("BEGIN")
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
        with _storage_failures(self.path):
            if not isinstance(expected_revision, SaveRevision):
                raise ValueError("Expected revision must use the application contract")
            revision = SaveRevision(expected_revision.value + 1)
            values = pet.capture_checkpoint()
            saved_settings, saved_adaptive = deepcopy(settings), deepcopy(adaptive)

            def commit_snapshot(
                connection: sqlite3.Connection, *, initial: bool
            ) -> SaveRevision:
                connection.execute("BEGIN IMMEDIATE")
                if initial:
                    connection.execute(
                        "INSERT INTO save_state VALUES (1, ?, ?, ?)",
                        (revision.value, values.updated_at, values.lived_seconds),
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
                    social_history=social_history,
                    world=world,
                    object_memory=object_memory,
                    world_recovery_x=world_recovery_x,
                )
                # Validate the complete result before commit or first publication.
                read_session_rows(connection, self._world_definitions())
                if read_rows(connection, "PRAGMA foreign_key_check"):
                    raise ValueError("Snapshot contains invalid owned relationships")
                connection.commit()
                return revision

            if self._exists():
                with open_database(self.path) as connection:
                    return commit_snapshot(connection, initial=False)
            if expected_revision.value != 0:
                raise StorageError(
                    StorageFailureKind.STALE_REVISION,
                    self.path,
                    "The expected saved checkpoint is missing",
                )
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with temporary_database(self.path) as temporary:
                with open_database(temporary, initialize=True) as connection:
                    commit_snapshot(connection, initial=True)
                publish_database(temporary, self.path)
            return revision
