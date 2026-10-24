"""Transactional version-one schema foundation, without domain row mappings.

Later mapping slices extend this first schema before runtime cutover. Migration
statements execute individually: executescript() would break rollback by
implicitly committing an existing transaction.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

from ...application.storage_contracts import StorageError, StorageFailureKind
from .pet_schema import PET_SCHEMA
from .relationship_schema import RELATIONSHIP_SCHEMA

APPLICATION_ID = 0x41494B4F  # AIKO, independent of schema version.
SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class SchemaMigration:
    version: int
    name: str
    statements: tuple[str, ...]


MIGRATIONS = (SchemaMigration(1, "initial_save_schema", (
    """CREATE TABLE schema_migrations (
        version INTEGER PRIMARY KEY CHECK (version > 0),
        name TEXT NOT NULL CHECK (length(name) > 0),
        applied_at REAL NOT NULL
            CHECK (applied_at >= 0 AND applied_at <= 1.7976931348623157e308)
    )""",
    """CREATE TABLE save_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        revision INTEGER NOT NULL
            CHECK (typeof(revision) = 'integer' AND revision > 0),
        updated_at REAL NOT NULL
            CHECK (updated_at >= 0 AND updated_at <= 1.7976931348623157e308),
        lived_seconds REAL NOT NULL
            CHECK (lived_seconds >= 0 AND lived_seconds <= 1.7976931348623157e308)
    )""",
) + PET_SCHEMA + RELATIONSHIP_SCHEMA),)


def _pragma_integer(connection: sqlite3.Connection, name: str) -> int:
    row = connection.execute(f"PRAGMA {name}").fetchone()
    if row is None or type(row[0]) is not int:
        raise ValueError(f"Invalid integer database metadata: {name}")
    value: int = row[0]
    return value


def _validate_history(connection: sqlite3.Connection, path: Path) -> None:
    try:
        rows = connection.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
        connection.execute(
            "SELECT id, revision, updated_at, lived_seconds FROM save_state LIMIT 0"
        )
    except sqlite3.DatabaseError as error:
        if getattr(error, "sqlite_errorcode", None) != sqlite3.SQLITE_ERROR:
            raise
        raise StorageError(StorageFailureKind.INVALID_DATABASE, path,
                           "Aiko schema metadata is incomplete") from error
    if rows != [(migration.version, migration.name) for migration in MIGRATIONS]:
        raise StorageError(StorageFailureKind.INVALID_DATABASE, path,
                           "Aiko schema history does not match its version")


def prepare_schema(
    connection: sqlite3.Connection, path: Path, *, initialize: bool = False,
) -> None:
    """Verify an existing Aiko schema, or initialize only a genuinely empty DB.

    No save checkpoint is invented. SQL-6 supplies the complete snapshot writer
    and consistent backups before any future user-schema upgrades are enabled.
    """
    connection.execute("BEGIN IMMEDIATE" if initialize else "BEGIN")
    try:
        identity = _pragma_integer(connection, "application_id")
        version = _pragma_integer(connection, "user_version")
        if identity != APPLICATION_ID:
            occupied = connection.execute(
                "SELECT 1 FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*' LIMIT 1"
            ).fetchone() is not None
            if not initialize or identity != 0 or version != 0 or occupied:
                raise StorageError(StorageFailureKind.INVALID_DATABASE, path,
                                   "This is not an initialized Aiko database")
            for migration in MIGRATIONS:
                for statement in migration.statements:
                    connection.execute(statement)
                connection.execute(
                    "INSERT INTO schema_migrations(version, name, applied_at) "
                    "VALUES (?, ?, ?)",
                    (migration.version, migration.name, time.time()),
                )
                connection.execute(f"PRAGMA user_version = {migration.version}")
            connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            version = _pragma_integer(connection, "user_version")
        if version != SCHEMA_VERSION:
            raise StorageError(StorageFailureKind.UNSUPPORTED_SCHEMA, path,
                               f"Unsupported Aiko database schema: {version}")
        _validate_history(connection, path)
        connection.commit()
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
