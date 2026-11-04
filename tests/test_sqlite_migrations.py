"""Synthetic future DDL proves consistent backups and failure rollback safely."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_candidates import (
    JokeExclusion,
)
from aiko_pet.application.social_content import (
    SocialCategory,
)
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.application.storage_contracts import (
    SaveRevision,
    StorageError,
    StorageFailureKind,
)
from aiko_pet.infrastructure.sqlite import schema
from aiko_pet.infrastructure.sqlite.backups import backup_database
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.schema import APPLICATION_ID, MIGRATIONS
from aiko_pet.infrastructure.sqlite.social_rows import (
    read_social_core,
    write_social_core,
)
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.state import PetState

TWO = SocialCategory.TWO_PARTS


class SqliteMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-migration-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        self.base_version = schema.SCHEMA_VERSION
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
                schema.SchemaMigration(
                    self.base_version + 1, "synthetic_future_upgrade", statements,
                ),
            ),
        )

    def backups(self) -> list[Path]:
        return list(self.path.parent.glob(
            f".{self.path.name}.schema-v{self.base_version}-*.sqlite3"
        ))

    def test_v1_receipts_upgrade_with_backup_and_preserved_session(self):
        original = self.store.load_session()
        history = SocialContentHistory((
            SocialContentReceipt(
                SocialCategory.FACT,
                "uselessfacts:legacy",
                "a" * 64,
            ),
        ))
        # Recreate the delivered v1 schema with its original transaction mapper.
        self.path.unlink()
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute(f"PRAGMA application_id={schema.APPLICATION_ID}")
            for statement in schema.MIGRATIONS[0].statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations VALUES (1,?,0)",
                (schema.MIGRATIONS[0].name,),
            )
            connection.execute("PRAGMA user_version=1")
            connection.execute(
                "INSERT INTO save_state VALUES (1,2,?,?)",
                (original.state.updated_at, original.state.lived_seconds),
            )
            # Populate unchanged owners using the current mapper. Settings,
            # online receipts and local-book rows need their delivered v1 shape.
            from aiko_pet.infrastructure.sqlite import session_rows
            from aiko_pet.infrastructure.sqlite.rows import upsert_singleton

            def write_v1_settings(connection, settings):
                row = settings.to_dict()
                del row['ui_scale_percent']
                upsert_singleton(connection, 'app_settings', row)

            with (
                patch.object(session_rows, "write_settings", write_v1_settings),
                patch.object(session_rows, "write_social_history"),
                patch.object(
                    session_rows,
                    "write_horoscope",
                ),
            ):
                session_rows.write_session_rows(
                    connection,
                    original.state.capture_checkpoint(),
                    original.settings,
                    adaptive=original.adaptive_memory,
                    social_history=history,
                    world=None,
                    object_memory=None,
                    world_recovery_x=0,
                )
            connection.execute(
                "INSERT INTO social_receipts VALUES (0,1,?,?,?)",
                ("fact", "uselessfacts:legacy", "a" * 64),
            )
            connection.commit()
        loaded = self.store.load_session()
        self.assertEqual(loaded.state, original.state)
        self.assertEqual(loaded.settings, original.settings)
        self.assertEqual(loaded.revision, SaveRevision(2))
        self.assertEqual(loaded.social_history, history)
        backups = list(self.path.parent.glob(f".{self.path.name}.schema-v1-*.sqlite3"))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone(), (1,))
            self.assertNotIn(
                "ui_scale_percent",
                [r[1] for r in connection.execute("PRAGMA table_info(app_settings)")],
            )
            self.assertNotIn(
                "intro_variant",
                [
                    r[1]
                    for r in connection.execute("PRAGMA table_info(social_receipts)")
                ],
            )
            self.assertEqual(
                connection.execute(
                    "SELECT identity, fingerprint FROM social_receipts"
                ).fetchall(),
                [("uselessfacts:legacy", "a" * 64)],
            )
        self.store.load_session()
        self.assertEqual(
            len(list(self.path.parent.glob(f".{self.path.name}.schema-v1-*.sqlite3"))),
            1,
        )

    def test_upgrade_creates_one_consistent_old_checkpoint_before_committing_schema(
        self,
    ) -> None:
        original = self.store.load_session()
        with (
            self.future(),
            patch.object(schema, "SCHEMA_VERSION", self.base_version + 1),
        ):
            loaded = self.store.load_session()
            self.assertEqual(loaded.state, original.state)
            self.assertEqual(loaded.revision, original.revision)
            with closing(sqlite3.connect(self.path)) as connection:
                self.assertEqual(
                    connection.execute("PRAGMA user_version").fetchone(),
                    (self.base_version + 1,),
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
        with (
            self.future(fail=True),
            patch.object(schema, "SCHEMA_VERSION", self.base_version + 1),
        ):
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
            patch.object(schema, "SCHEMA_VERSION", self.base_version + 1),
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
            backup = backup_database(self.path, self.base_version)
            self.assertEqual(SqliteStateStore(backup).load_session().state.satiety, 17)

    def test_locked_backup_aborts_promptly_and_removes_the_incomplete_copy(
        self,
    ) -> None:
        with closing(sqlite3.connect(self.path)) as writer:
            writer.execute("BEGIN EXCLUSIVE")
            try:
                with self.assertRaises(StorageError) as failure:
                    backup_database(self.path, self.base_version)
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

    def test_v3_database_migration_preserves_receipts_and_old_provider_pause(self):
        now = 1_800_000_000.0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v3.sqlite3"
            with closing(sqlite3.connect(path)) as connection:
                connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
                for migration in MIGRATIONS[:3]:
                    for statement in migration.statements:
                        connection.execute(statement)
                    connection.execute("INSERT INTO schema_migrations VALUES (?,?,?)",
                                       (migration.version, migration.name, now))
                connection.execute("PRAGMA user_version=3")
                connection.execute("INSERT INTO save_state VALUES (1,1,?,0)",
                                   (now,))
                connection.execute("INSERT INTO social_receipts VALUES (0,1,?,?,?,0)",
                                   ("twopart", "jokeapi:1", "a" * 64))
                connection.execute(
                    "INSERT INTO provider_pauses VALUES ('jokeapi',1,0,?)",
                    (now + 60,),
                )
                connection.commit()
            with open_database(path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                history = read_social_core(connection)
                self.assertEqual(history.entries[0].identity, "jokeapi:1")
                self.assertEqual(history.requests.blocks[0].until, now + 60)
                self.assertEqual(history.exclusions, ())
                history = history.excluded(
                    JokeExclusion(TWO, 2, 2, "format", now + 3600), now,
                )
                write_social_core(connection, history)
                connection.commit()
            with open_database(path) as connection:
                connection.execute("BEGIN")
                self.assertEqual(read_social_core(connection), history)


if __name__ == "__main__":
    unittest.main()
