"""Unchanged legacy bytes and consistent private pre-schema-update backups."""

from __future__ import annotations

import os
import sqlite3
import tempfile
import uuid
from contextlib import closing, suppress
from pathlib import Path

from ...application.storage_contracts import StorageError, StorageFailureKind
from .errors import translate_storage_error


def backup_legacy_json(path: Path, contents: bytes) -> Path:
    """Back up exactly the bytes validated for import; never alter the source."""
    backup = path.with_name(f"{path.stem}-{uuid.uuid4().hex}.aiko-save-backup")
    created = False
    complete = False
    try:
        with backup.open("xb") as file:
            created = True
            file.write(contents)
            file.flush()
            os.fsync(file.fileno())
        complete = True
        return backup
    finally:
        if created and not complete:
            with suppress(OSError):
                backup.unlink(missing_ok=True)


def backup_database(path: Path, version: int) -> Path:
    """Use a separate reader while the migration owner holds its reserved lock.

    Never call backup() on a connection with an active write transaction. Abort
    busy/locked backup steps immediately rather than sleeping/retrying forever.
    """
    destination: Path | None = None
    complete = False
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{path.name}.schema-v{version}-",
            suffix=".sqlite3",
            dir=path.parent,
        )
        os.close(descriptor)
        destination = Path(name)
        with (
            closing(
                sqlite3.connect(
                    path.absolute().as_uri() + "?mode=ro", uri=True, timeout=0
                )
            ) as source,
            closing(sqlite3.connect(destination, timeout=0)) as target,
        ):

            def progress(status: int, _remaining: int, _total: int) -> None:
                if status in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                    raise StorageError(
                        StorageFailureKind.LOCKED, path, "Database backup is locked"
                    )

            source.backup(target, pages=128, progress=progress, sleep=0)
            if target.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                raise StorageError(
                    StorageFailureKind.INVALID_DATABASE,
                    path,
                    "Consistent schema backup failed validation",
                )
        complete = True
        return destination
    except (sqlite3.Error, OSError) as error:
        raise translate_storage_error(error, path) from error
    finally:
        if destination is not None and not complete:
            with suppress(OSError):
                destination.unlink(missing_ok=True)
