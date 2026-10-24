"""Translate native storage errors at the infrastructure boundary."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from ...application.storage_contracts import StorageError, StorageFailureKind


def translate_storage_error(error: sqlite3.Error | OSError, path: Path) -> StorageError:
    if isinstance(error, PermissionError):
        kind = StorageFailureKind.ACCESS
    elif isinstance(error, OSError):
        kind = StorageFailureKind.IO
    else:
        code = getattr(error, "sqlite_errorcode", 0)
        primary = code & 0xFF if isinstance(code, int) else 0
        if primary in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            kind = StorageFailureKind.LOCKED
        elif primary in (
            sqlite3.SQLITE_READONLY, sqlite3.SQLITE_PERM, sqlite3.SQLITE_AUTH,
        ):
            kind = StorageFailureKind.ACCESS
        elif primary in (
            sqlite3.SQLITE_IOERR, sqlite3.SQLITE_CANTOPEN, sqlite3.SQLITE_FULL,
        ):
            kind = StorageFailureKind.IO
        elif primary in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB):
            kind = StorageFailureKind.INVALID_DATABASE
        elif isinstance(error, sqlite3.IntegrityError) or primary in (
            sqlite3.SQLITE_CONSTRAINT, sqlite3.SQLITE_MISMATCH, sqlite3.SQLITE_RANGE,
        ):
            kind = StorageFailureKind.INVALID_DATA
        else:
            kind = StorageFailureKind.DATABASE
    return StorageError(kind, path, str(error))
