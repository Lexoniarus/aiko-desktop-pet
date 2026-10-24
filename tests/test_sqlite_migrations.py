"""Synthetic future DDL proves consistent backups and failure rollback safely."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import (
    SaveRevision,
    StorageError,
    StorageFailureKind,
)
from aiko_pet.infrastructure.sqlite import schema
from aiko_pet.infrastructure.sqlite.backups import backup_database
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.state import PetState


class SqliteMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-migration-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        self.store = self.create_store(self.path)

    @staticmethod
    def create_store(path: Path) -> SqliteStateStore:
        store = SqliteStateStore(path)
        store.save(
            PetState(satiety=41, updated_at=1800000000, lived_seconds=90000),
            PetSettings(zodiac_sign="leo"),
            expected_revision=SaveRevision(),
            adaptive=AdaptiveMemory(),
            social_history=SocialContentHistory(),
        )
        return store

    def future(self, *, fail: bool = False):
        statements = (
            "CREATE TABLE upgrade_probe(value TEXT)",
            "INVALID SQL" if fail else "INSERT INTO upgrade_probe VALUES ('done')",
        )
        return patch.object(
            schema,
            "MIGRATIONS",
            (
                *schema.MIGRATIONS,
                schema.SchemaMigration(2, "synthetic_future_upgrade", statements),
            ),
        )

    def backups(self) -> list[Path]:
        return list(self.path.parent.glob(f".{self.path.name}.schema-v1-*.sqlite3"))

    def test_upgrade_creates_one_consistent_old_checkpoint_before_committing_schema(
        self,
    ) -> None:
        original = self.store.load_session()
        with self.future(), patch.object(schema, "SCHEMA_VERSION", 2):
            loaded = self.store.load_session()
            self.assertEqual(loaded.state, original.state)
            self.assertEqual(loaded.revision, original.revision)
            with closing(sqlite3.connect(self.path)) as connection:
                self.assertEqual(
                    connection.execute("PRAGMA user_version").fetchone(), (2,)
                )
                self.assertEqual(
                    connection.execute("SELECT value FROM upgrade_probe").fetchone(),
                    ("done",),
                )
            self.store.load_session()
            self.assertEqual(len(self.backups()), 1)
        saved = SqliteStateStore(self.backups()[0]).load_session()
        self.assertEqual(
            (saved.state, saved.settings, saved.revision),
            (original.state, original.settings, original.revision),
        )

    def test_failed_upgrade_keeps_old_database_and_the_valid_backup(self) -> None:
        before = self.path.read_bytes()
        with self.future(fail=True), patch.object(schema, "SCHEMA_VERSION", 2):
            with self.assertRaises(StorageError):
                self.store.load_session()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.store.load_session().revision, SaveRevision(1))
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual(
            SqliteStateStore(self.backups()[0]).load_session().state.satiety, 41
        )

    def test_backup_failure_stops_upgrade_before_any_schema_change(self) -> None:
        before = self.path.read_bytes()
        failure = StorageError(StorageFailureKind.ACCESS, self.path, "Backup denied")
        with (
            self.future(),
            patch.object(schema, "SCHEMA_VERSION", 2),
            patch.object(
                schema,
                "backup_database",
                side_effect=failure,
            ),
        ):
            with self.assertRaises(StorageError) as caught:
                self.store.load_session()
        self.assertEqual(caught.exception.kind, StorageFailureKind.ACCESS)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.backups(), [])

    def test_backup_includes_committed_wal_rows_without_copying_raw_files(self) -> None:
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute("PRAGMA journal_mode = WAL")
            writer.execute("PRAGMA wal_autocheckpoint = 0")
            writer.execute("UPDATE pet_state SET satiety = 17")
            writer.commit()
            self.assertTrue(Path(str(self.path) + "-wal").exists())
            backup = backup_database(self.path, 1)
            self.assertEqual(SqliteStateStore(backup).load_session().state.satiety, 17)

    def test_locked_backup_aborts_promptly_and_removes_the_incomplete_copy(
        self,
    ) -> None:
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute("BEGIN EXCLUSIVE")
            try:
                with self.assertRaises(StorageError) as failure:
                    backup_database(self.path, 1)
                self.assertEqual(failure.exception.kind, StorageFailureKind.LOCKED)
            finally:
                writer.rollback()
        self.assertEqual(self.backups(), [])

    def test_missing_tables_indexes_and_dangling_relationships_cannot_be_overwritten(
        self,
    ) -> None:
        for index, statement in enumerate((
            "DROP TABLE adaptive_hour_slots",
            "DROP INDEX moodlet_cause_semantic_receipt",
            "INSERT INTO object_memory_sources VALUES ('missing', 'other', 0)",
        )):
            with self.subTest(statement=statement):
                path = self.path.with_name(f"invalid-{index}.sqlite3")
                store = self.create_store(path)
                with closing(sqlite3.connect(path)) as connection:
                    connection.execute(statement)
                    connection.commit()
                before = path.read_bytes()
                with self.assertRaises(StorageError) as failure:
                    store.load_session()
                self.assertEqual(
                    failure.exception.kind, StorageFailureKind.INVALID_DATABASE
                )
                with self.assertRaises(StorageError):
                    store.save(
                        PetState(updated_at=1800000000),
                        PetSettings(),
                        expected_revision=SaveRevision(1),
                        adaptive=AdaptiveMemory(),
                        social_history=SocialContentHistory(),
                    )
                self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
