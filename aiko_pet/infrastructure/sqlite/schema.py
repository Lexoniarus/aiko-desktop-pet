"""Transactional versioned schema foundation, without domain row mappings.

The delivered version-one DDL remains unchanged. Migration statements execute
individually: executescript() would break rollback by
implicitly committing an existing transaction.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ...application.storage_contracts import StorageError, StorageFailureKind
from .adaptive_schema import ADAPTIVE_SCHEMA
from .backups import backup_database
from .care_evidence_schema import CARE_EVIDENCE_SCHEMA
from .food_handover_schema import FOOD_HANDOVER_SCHEMA
from .horoscope_schema import HOROSCOPE_SCHEMA, LOCAL_HOROSCOPE_SCHEMA
from .interaction_schema import INTERACTION_SCHEMA
from .moodlet_schema import MOODLET_SCHEMA
from .pet_schema import PET_SCHEMA
from .relationship_schema import RELATIONSHIP_SCHEMA
from .social_schema import SOCIAL_SCHEMA
from .wish_schema import WISH_SCHEMA
from .world_schema import WORLD_SCHEMA

APPLICATION_ID = 0x41494B4F  # AIKO, independent of schema version.
SCHEMA_VERSION = 4
SnapshotTransaction = Literal["read", "write"]

_DOMAIN_SCHEMA = (
    PET_SCHEMA
    + RELATIONSHIP_SCHEMA
    + WORLD_SCHEMA
    + WISH_SCHEMA
    + FOOD_HANDOVER_SCHEMA
    + MOODLET_SCHEMA
    + INTERACTION_SCHEMA
    + CARE_EVIDENCE_SCHEMA
    + ADAPTIVE_SCHEMA
    + SOCIAL_SCHEMA
    + HOROSCOPE_SCHEMA
)


@dataclass(frozen=True, slots=True)
class SchemaMigration:
    version: int
    name: str
    statements: tuple[str, ...]


MIGRATIONS = (
    SchemaMigration(
        1,
        "initial_save_schema",
        (
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
            """CREATE TABLE import_provenance (
        save_id INTEGER PRIMARY KEY CHECK (save_id = 1)
            REFERENCES save_state(id) ON DELETE CASCADE,
        source_format TEXT NOT NULL CHECK (source_format = 'json-v1'),
        imported_at REAL NOT NULL
            CHECK (imported_at >= 0 AND imported_at <= 1.7976931348623157e308)
    )""",
        )
        + _DOMAIN_SCHEMA,
    ),
    SchemaMigration(
        2,
        "social_introduction_rotation",
        (
            "ALTER TABLE social_receipts ADD COLUMN intro_variant INTEGER "
            "CHECK(intro_variant IS NULL OR "
            "(typeof(intro_variant) = 'integer' AND intro_variant BETWEEN 0 AND 2))",
        ),
    ),
    SchemaMigration(
        3,
        "local_horoscope_book",
        LOCAL_HOROSCOPE_SCHEMA
        + (
            "INSERT INTO local_horoscope_days("
            "day,state_id,sign,progress_index,admitted,completed) "
            "SELECT day,state_id,sign,0,admitted,completed FROM horoscope_days "
            "WHERE admitted=1",
            "DROP TABLE horoscope_days",
            "ALTER TABLE world_objects ADD COLUMN expires_at REAL "
            "CHECK(expires_at >= 0)",
            "CREATE TEMP TABLE saved_book_sources AS "
            "SELECT * FROM object_memory_sources",
            "DROP TABLE object_memory_sources",
            "ALTER TABLE object_memories RENAME TO previous_object_memories",
            WORLD_SCHEMA[3].replace("('food', 'drink')", "('food', 'drink', 'book')"),
            "INSERT INTO object_memories SELECT * FROM previous_object_memories",
            "DROP TABLE previous_object_memories",
            WORLD_SCHEMA[4],
            "INSERT INTO object_memory_sources SELECT * FROM saved_book_sources",
            "DROP TABLE saved_book_sources",
        ),
    ),
    SchemaMigration(
        4,
        "joke_candidate_exclusions",
        ("""CREATE TABLE joke_exclusions (
            position_index INTEGER PRIMARY KEY CHECK(position_index >= 0),
            state_id INTEGER NOT NULL REFERENCES save_state(id) ON DELETE CASCADE
                CHECK(state_id = 1),
            category TEXT NOT NULL CHECK(category IN ('single', 'twopart')),
            lower INTEGER NOT NULL CHECK(lower >= 0),
            upper INTEGER NOT NULL CHECK(upper >= lower AND upper <= 100000),
            reason TEXT NOT NULL,
            until REAL NOT NULL CHECK(until >= 0),
            revision INTEGER NOT NULL CHECK(revision > 0),
            UNIQUE(category, lower, upper)
        )""",),
    ),
)


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
        raise StorageError(
            StorageFailureKind.INVALID_DATABASE,
            path,
            "Aiko schema metadata is incomplete",
        ) from error
    version = _pragma_integer(connection, "user_version")
    if rows != [
        (migration.version, migration.name)
        for migration in MIGRATIONS
        if migration.version <= version
    ]:
        raise StorageError(
            StorageFailureKind.INVALID_DATABASE,
            path,
            "Aiko schema history does not match its version",
        )


def _supported_version(connection: sqlite3.Connection, path: Path) -> int:
    if _pragma_integer(connection, "application_id") != APPLICATION_ID:
        raise StorageError(
            StorageFailureKind.INVALID_DATABASE,
            path,
            "This is not an initialized Aiko database",
        )
    version = _pragma_integer(connection, "user_version")
    if not 1 <= version <= SCHEMA_VERSION:
        raise StorageError(
            StorageFailureKind.UNSUPPORTED_SCHEMA,
            path,
            f"Unsupported Aiko database schema: {version}",
        )
    _validate_history(connection, path)
    return version


def _validate_structure(
    connection: sqlite3.Connection,
    path: Path,
    version: int,
) -> None:
    # DDL is the canonical table inventory; no second hand-maintained field model.
    statements = tuple(
        statement
        for migration in MIGRATIONS
        if migration.version <= version
        for statement in migration.statements
    )
    required: set[tuple[str, str]] = set()
    for statement in statements:
        words = statement.split()
        if statement.startswith("CREATE TABLE "):
            required.add(("table", words[2].partition("(")[0]))
        elif statement.startswith("CREATE UNIQUE INDEX "):
            required.add(("index", words[3]))
        elif statement.startswith("CREATE INDEX "):
            required.add(("index", words[2]))
        elif statement.startswith("DROP TABLE "):
            required.discard(("table", words[2]))
        elif statement.startswith("ALTER TABLE ") and " RENAME TO " in statement:
            required.discard(("table", words[2]))
            required.add(("table", words[-1]))
    present = set(connection.execute("SELECT type, name FROM sqlite_schema"))
    if not required <= present:
        raise StorageError(
            StorageFailureKind.INVALID_DATABASE,
            path,
            "Required Aiko snapshot tables or indexes are missing",
        )
    if (
        connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]
        or connection.execute("PRAGMA foreign_key_check").fetchone() is not None
    ):
        raise StorageError(
            StorageFailureKind.INVALID_DATABASE,
            path,
            "Aiko database integrity validation failed",
        )


def _apply_migrations(connection: sqlite3.Connection, after: int) -> None:
    for migration in MIGRATIONS:
        if migration.version <= after:
            continue
        for statement in migration.statements:
            connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations(version, name, applied_at) VALUES (?, ?, ?)",
            (migration.version, migration.name, time.time()),
        )
        connection.execute(f"PRAGMA user_version = {migration.version}")


def prepare_schema(
    connection: sqlite3.Connection,
    path: Path,
    *,
    initialize: bool = False,
    transaction: SnapshotTransaction | None = None,
) -> None:
    """Validate/migrate once, optionally retaining the caller's snapshot transaction."""
    if transaction not in (None, "read", "write"):
        raise ValueError("Invalid snapshot transaction kind")
    begin = "BEGIN IMMEDIATE" if initialize or transaction == "write" else "BEGIN"
    connection.execute(begin)
    try:
        identity = _pragma_integer(connection, "application_id")
        version = _pragma_integer(connection, "user_version")
        if identity != APPLICATION_ID:
            occupied = (
                connection.execute(
                    "SELECT 1 FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*' LIMIT 1"
                ).fetchone()
                is not None
            )
            if not initialize or identity != 0 or version != 0 or occupied:
                raise StorageError(
                    StorageFailureKind.INVALID_DATABASE,
                    path,
                    "This is not an initialized Aiko database",
                )
            _apply_migrations(connection, after=0)
            connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
        version = _supported_version(connection, path)
        _validate_structure(connection, path, version)
        if version < SCHEMA_VERSION:
            if not initialize and transaction != "write":
                # Recheck after acquiring the writer lock: another opener may upgrade.
                connection.commit()
                connection.execute("BEGIN IMMEDIATE")
                version = _supported_version(connection, path)
                _validate_structure(connection, path, version)
            if version < SCHEMA_VERSION:
                backup_database(path, version)
                _apply_migrations(connection, after=version)
                version = _supported_version(connection, path)
                _validate_structure(connection, path, version)
        if transaction is None:
            connection.commit()
    except BaseException:
        if connection.in_transaction:
            connection.rollback()
        raise
