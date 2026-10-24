"""Own one SQLite connection, enforce foreign keys and translate failures.

Paths are explicit; opening never searches for JSON, creates parent directories
or falls back to another save. Native operations fail promptly when locked;
appropriate retry/reporting belongs to the later persistence coordinator.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from ...application.storage_contracts import StorageError, StorageFailureKind
from .errors import translate_storage_error
from .schema import prepare_schema


@contextmanager
def open_database(
    path: Path, *, initialize: bool = False,
) -> Iterator[sqlite3.Connection]:
    """Open an existing save; creating an empty schema requires explicit opt-in.

    Callers own snapshot transactions. Exiting never commits pending caller
    writes; close rolls back any unfinished transaction even after an error.
    """
    mode = "rwc" if initialize else "rw"
    try:
        connection = sqlite3.connect(
            path.absolute().as_uri() + f"?mode={mode}",
            uri=True, isolation_level=None, timeout=0,
        )
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
                raise StorageError(StorageFailureKind.DATABASE, path,
                                   "SQLite foreign-key enforcement is unavailable")
            prepare_schema(connection, path, initialize=initialize)
            yield connection
        finally:
            connection.close()
    except (sqlite3.Error, OSError) as error:
        raise translate_storage_error(error, path) from error
