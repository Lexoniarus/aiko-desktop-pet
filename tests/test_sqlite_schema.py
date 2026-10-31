"""Transactional schema checks use temporary files and never load a pet session."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.storage_contracts import StorageError, StorageFailureKind
from aiko_pet.infrastructure.sqlite import schema
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.errors import translate_storage_error


class SqliteSchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-schema-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "save # ü.sqlite3"

    def test_initialize_and_reopen_preserve_identity_without_inventing_checkpoint(
        self,
    ) -> None:
        with open_database(self.path, initialize=True) as connection:
            self.assertEqual(connection.execute("PRAGMA application_id").fetchone(),
                             (schema.APPLICATION_ID,))
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone(),
                             (schema.SCHEMA_VERSION,))
            self.assertEqual(connection.execute(
                "SELECT version, name FROM schema_migrations"
            ).fetchall(), [(m.version, m.name) for m in schema.MIGRATIONS])
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM save_state"
            ).fetchone(), (0,))
        original = self.path.read_bytes()
        with open_database(self.path) as connection:
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone(), (1,))
        self.assertEqual(self.path.read_bytes(), original)

    def test_missing_and_uninitialized_databases_are_not_silently_created(self) -> None:
        with self.assertRaises(StorageError) as failure:
            with open_database(self.path):
                self.fail("Missing database must not be opened")
        self.assertEqual(failure.exception.kind, StorageFailureKind.IO)
        self.assertFalse(self.path.exists())
        with closing(sqlite3.connect(self.path)):
            pass
        with self.assertRaises(StorageError) as failure:
            with open_database(self.path):
                self.fail("Uninitialized database requires explicit initialization")
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATABASE)
        self.assertEqual(self.path.stat().st_size, 0)

    def test_foreign_databases_are_never_adopted_or_overwritten(self) -> None:
        for name, identity, version in (("foreign_data", 0, 0), ("sqliteXdata", 0, 0),
                                        ("other_app", 123, 1)):
            with self.subTest(name=name):
                path = self.path.with_name(name + ".sqlite3")
                with closing(sqlite3.connect(path)) as connection:
                    connection.execute(f"CREATE TABLE {name}(value TEXT)")
                    connection.execute(f"PRAGMA application_id = {identity}")
                    connection.execute(f"PRAGMA user_version = {version}")
                    connection.commit()
                original = path.read_bytes()
                with self.assertRaises(StorageError) as failure:
                    with open_database(path, initialize=True):
                        self.fail("Existing foreign data must not be adopted")
                self.assertEqual(failure.exception.kind,
                                 StorageFailureKind.INVALID_DATABASE)
                self.assertEqual(path.read_bytes(), original)

    def test_invalid_file_and_future_schema_are_reported_without_changes(self) -> None:
        self.path.write_bytes(b"This is not a SQLite save")
        original = self.path.read_bytes()
        with self.assertRaises(StorageError) as failure:
            with open_database(self.path, initialize=True):
                self.fail("Invalid file must not be replaced")
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATABASE)
        self.assertEqual(self.path.read_bytes(), original)
        self.path.unlink()
        with open_database(self.path, initialize=True) as connection:
            connection.execute("PRAGMA user_version = 999")
        original = self.path.read_bytes()
        with self.assertRaises(StorageError) as failure:
            with open_database(self.path, initialize=True):
                self.fail("Future schema must not be downgraded")
        self.assertEqual(failure.exception.kind, StorageFailureKind.UNSUPPORTED_SCHEMA)
        self.assertEqual(self.path.read_bytes(), original)

    def test_missing_or_mismatched_schema_history_is_invalid(self) -> None:
        for statement in (
            "DROP TABLE schema_migrations",
            "UPDATE schema_migrations SET name = 'different'",
            "DROP TABLE save_state",
        ):
            with self.subTest(statement=statement):
                path = self.path.with_name(str(len(statement)) + ".sqlite3")
                with open_database(path, initialize=True) as connection:
                    connection.execute(statement)
                original = path.read_bytes()
                with self.assertRaises(StorageError) as failure:
                    with open_database(path):
                        self.fail("Incomplete schema must not be loaded")
                self.assertEqual(failure.exception.kind,
                                 StorageFailureKind.INVALID_DATABASE)
                self.assertEqual(path.read_bytes(), original)

    def test_failed_ddl_and_final_validation_roll_back_schema_and_version(self) -> None:
        first = schema.MIGRATIONS[0]
        patches = (
            patch.object(schema, "MIGRATIONS", (first, schema.SchemaMigration(
                2, "injected_failure", ("CREATE TABLE transient(value TEXT)",
                                        "INVALID SQL"),
            ))),
            patch.object(schema, "_validate_history", side_effect=StorageError(
                StorageFailureKind.INVALID_DATABASE, self.path,
                "Injected final validation failure",
            )),
        )
        for index, injection in enumerate(patches):
            with self.subTest(index=index), injection:
                path = self.path.with_name(f"rollback-{index}.sqlite3")
                with self.assertRaises(StorageError):
                    with open_database(path, initialize=True):
                        self.fail("Failed migration must never be published")
                with closing(sqlite3.connect(path)) as connection:
                    self.assertEqual(connection.execute(
                        "SELECT name FROM sqlite_schema"
                    ).fetchall(), [])
                    for pragma in ("user_version", "application_id"):
                        self.assertEqual(connection.execute(
                            f"PRAGMA {pragma}"
                        ).fetchone(), (0,))

    def test_constraints_and_owned_foreign_keys_are_enforced_on_each_connection(
        self,
    ) -> None:
        with open_database(self.path, initialize=True) as connection:
            connection.execute(
                "CREATE TABLE fixture_child (save_id INTEGER NOT NULL "
                "REFERENCES save_state(id) ON DELETE CASCADE)"
            )
        for statement in (
            "INSERT INTO save_state VALUES (2, 1, 100, 10)",
            "INSERT INTO save_state VALUES (1, 0, 100, 10)",
            "INSERT INTO save_state VALUES (1, 1, 100, -1)",
            "INSERT INTO fixture_child VALUES (1)",
        ):
            with self.subTest(statement=statement):
                with self.assertRaises(StorageError) as failure:
                    with open_database(self.path) as connection:
                        connection.execute(statement)
                self.assertEqual(failure.exception.kind,
                                 StorageFailureKind.INVALID_DATA)
        with open_database(self.path) as connection:
            connection.execute("INSERT INTO save_state VALUES (1, 1, 100, 10)")
            connection.execute("INSERT INTO fixture_child VALUES (1)")
            connection.execute("DELETE FROM save_state")
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM fixture_child"
            ).fetchone(), (0,))

    def test_locked_database_returns_typed_failure_without_waiting(self) -> None:
        with open_database(self.path, initialize=True):
            pass
        with closing(sqlite3.connect(self.path)) as blocker:
            blocker.execute("BEGIN EXCLUSIVE")
            try:
                with self.assertRaises(StorageError) as failure:
                    with open_database(self.path):
                        self.fail("Locked database must not open")
                self.assertEqual(failure.exception.kind, StorageFailureKind.LOCKED)
                self.assertEqual(failure.exception.path, self.path)
            finally:
                blocker.rollback()
        with open_database(self.path):
            pass

    def test_uncommitted_caller_transaction_is_not_saved_on_exit(self) -> None:
        with open_database(self.path, initialize=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("INSERT INTO save_state VALUES (1, 1, 100, 10)")
        with open_database(self.path) as connection:
            self.assertEqual(connection.execute(
                "SELECT count(*) FROM save_state"
            ).fetchone(), (0,))

    def test_extended_backend_errors_use_stable_application_reasons(self) -> None:
        for code, kind in (
            (sqlite3.SQLITE_BUSY | (2 << 8), StorageFailureKind.LOCKED),
            (sqlite3.SQLITE_IOERR | (1 << 8), StorageFailureKind.IO),
            (sqlite3.SQLITE_READONLY, StorageFailureKind.ACCESS),
        ):
            with self.subTest(code=code):
                error = sqlite3.OperationalError("Backend detail")
                setattr(error, "sqlite_errorcode", code)
                self.assertEqual(translate_storage_error(error, self.path).kind, kind)
        self.assertEqual(translate_storage_error(
            PermissionError("Denied"), self.path,
        ).kind, StorageFailureKind.ACCESS)


if __name__ == "__main__":
    unittest.main()
