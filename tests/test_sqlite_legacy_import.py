"""Import is backed up, atomic, strict and subordinate to existing SQLite."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from test_emotional_persistence import wish_state
from test_legacy_json_codec import WALL, definitions, legacy_payload

from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import (
    SaveRevision,
    StorageError,
    StorageFailureKind,
)
from aiko_pet.infrastructure.legacy_json_codec import decode_legacy_session
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.infrastructure.save_paths import SavePaths
from aiko_pet.infrastructure.sqlite import backups, legacy_import
from aiko_pet.infrastructure.sqlite import store as store_module
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.legacy_import import load_or_import_session
from aiko_pet.infrastructure.sqlite.publication import publish_database
from aiko_pet.infrastructure.sqlite.session_rows import write_session_rows
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.infrastructure.wish_codec import encode_wishes
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.state import PetState


class SqliteLegacyImportTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-legacy-import-")
        self.addCleanup(folder.cleanup)
        self.paths = SavePaths(
            Path(folder.name) / "save.sqlite3", Path(folder.name) / "save.json"
        )
        self.definitions = definitions()
        self.store = SqliteStateStore(self.paths.database, definitions=self.definitions)

    def source(self, contents: bytes | None = None) -> bytes:
        data = (
            json.dumps(legacy_payload(), ensure_ascii=False, indent=2)
            .replace("\n", "\r\n")
            .encode("utf-8")
            if contents is None
            else contents
        )
        self.paths.legacy_json.write_bytes(data)
        return data

    def load(self):
        return load_or_import_session(
            self.paths, now=WALL + 3600, definitions=self.definitions
        )

    def backups(self) -> list[Path]:
        return list(self.paths.legacy_json.parent.glob("*.aiko-save-backup"))

    def save_winner(self) -> None:
        self.store.save(
            PetState(satiety=12, updated_at=WALL),
            PetSettings(),
            expected_revision=SaveRevision(),
            adaptive=AdaptiveMemory(),
            social_history=SocialContentHistory(),
        )

    def test_full_import_preserves_bytes_owners_and_provenance_across_later_saves(
        self,
    ) -> None:
        contents = self.source()
        expected = decode_legacy_session(contents, self.definitions, now=WALL + 3600)
        with patch.object(
            PetState, "advance", side_effect=AssertionError("No simulation")
        ):
            loaded = self.load()
        self.assertEqual(
            loaded.state.capture_checkpoint(), expected.state.capture_checkpoint()
        )
        self.assertEqual(
            (loaded.world, loaded.object_memory),
            (expected.world, expected.object_memory),
        )
        self.assertEqual(
            (loaded.settings, loaded.adaptive_memory, loaded.social_history),
            (expected.settings, expected.adaptive_memory, expected.social_history),
        )
        self.assertEqual(loaded.revision, SaveRevision(1))
        self.assertEqual(self.paths.legacy_json.read_bytes(), contents)
        self.assertEqual(len(self.backups()), 1)
        self.assertEqual(self.backups()[0].read_bytes(), contents)
        with open_database(self.paths.database) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT source_format, imported_at FROM import_provenance"
                ).fetchall(),
                [("json-v1", WALL + 3600)],
            )
        self.store.save(
            loaded.state,
            loaded.settings,
            expected_revision=loaded.revision,
            adaptive=loaded.adaptive_memory,
            social_history=loaded.social_history,
            world=loaded.world,
            object_memory=loaded.object_memory,
        )
        with open_database(self.paths.database) as connection:
            self.assertEqual(
                connection.execute("SELECT count(*) FROM import_provenance").fetchone(),
                (1,),
            )
        self.assertEqual(self.paths.legacy_json.read_bytes(), contents)
        self.assertEqual(list(self.paths.database.parent.glob(".aiko-*")), [])

    def test_missing_saves_do_not_create_files_and_minimal_old_json_imports(
        self,
    ) -> None:
        fresh = self.load()
        self.assertFalse(fresh.restored_from_save)
        self.assertEqual(fresh.revision, SaveRevision())
        self.assertEqual(list(self.paths.database.parent.iterdir()), [])
        self.source(b'{"version":1,"pet":{"satiety":42,"updated_at":1800000000}}')
        loaded = self.load()
        self.assertEqual((loaded.state.satiety, loaded.state.lived_seconds), (42, 0))
        self.assertIsNone(loaded.state.friendship_history.baseline)

    def test_supported_old_subformats_keep_goals_and_do_not_invent_causes(self) -> None:
        raw = legacy_payload()
        raw["pet"]["wishes"] = encode_wishes(wish_state())
        for wish in raw["pet"]["wishes"]["active"]:
            for field in ("goal", "target", "pinned"):
                del wish[field]
            del wish["game"]["completed_rounds"]
        for episode in raw["pet"]["moodlets"]["active"]:
            del episode["causes"], episode["attribution"]
        raw["social_history"]["version"] = 1
        del raw["social_history"]["requests"], raw["social_history"]["horoscope"]
        for receipt in raw["social_history"]["entries"]:
            del receipt["intro_variant"]
        raw["object_memory"]["version"] = 2
        for entry in raw["object_memory"]["entries"]:
            del entry["instance_id"]
        self.source(json.dumps(raw).encode())
        loaded = self.load()
        self.assertEqual(loaded.state.wishes.active, wish_state().active)
        self.assertTrue(loaded.social_history.entries)
        self.assertTrue(all(r.intro_variant is None
                            for r in loaded.social_history.entries))
        self.assertIsNone(loaded.social_history.horoscope)
        self.assertIsNotNone(loaded.object_memory)
        assert loaded.object_memory is not None
        self.assertIsNone(loaded.object_memory.entries[0].instance_id)
        for episode in loaded.state.moodlets.active:
            self.assertEqual(len(episode.causes), 1)
            self.assertIsNone(episode.causes[0].wish)

    def test_invalid_source_stops_before_backup_or_publication(self) -> None:
        for contents in (
            b"{",
            b"\xff",
            b'{"version":2,"pet":{}}',
            b'{"version":1,"pet":{"moodlets":{}}}',
            b'{"version":1,"pet":{},"settings":{"scale":99}}',
            b'{"version":1,"pet":{},"social_history":null}',
        ):
            with self.subTest(contents=contents):
                self.source(contents)
                with self.assertRaises(StorageError) as failure:
                    self.load()
                self.assertEqual(
                    failure.exception.kind, StorageFailureKind.INVALID_DATA
                )
                self.assertEqual(failure.exception.path, self.paths.legacy_json)
                self.assertFalse(self.paths.database.exists())
                self.assertEqual(self.paths.legacy_json.read_bytes(), contents)
                self.assertEqual(self.backups(), [])

    def test_existing_sqlite_ignores_even_unreadable_or_malformed_neighbor_json(
        self,
    ) -> None:
        self.source()
        first = self.load()
        self.source(b"not JSON")
        with patch.object(Path, "read_bytes", side_effect=PermissionError("Denied")):
            loaded = self.load()
        self.assertEqual(
            loaded.state.capture_checkpoint(), first.state.capture_checkpoint()
        )
        self.assertEqual(loaded.revision, first.revision)
        self.assertEqual(len(self.backups()), 1)

    def test_invalid_foreign_newer_and_incomplete_databases_never_fall_back(
        self,
    ) -> None:
        self.source()
        for kind in ("corrupt", "foreign", "newer", "incomplete"):
            with self.subTest(kind=kind):
                self.paths.database.unlink(missing_ok=True)
                if kind == "corrupt":
                    self.paths.database.write_bytes(b"Not SQLite")
                elif kind == "foreign":
                    with closing(sqlite3.connect(self.paths.database)) as connection:
                        connection.execute("CREATE TABLE other (id INTEGER)")
                        connection.commit()
                else:
                    self.save_winner()
                    with closing(sqlite3.connect(self.paths.database)) as connection:
                        connection.execute(
                            "PRAGMA user_version = 99"
                            if kind == "newer"
                            else "DROP TABLE wish_instances"
                        )
                        connection.commit()
                before = self.paths.database.read_bytes()
                with self.assertRaises(StorageError):
                    self.load()
                self.assertEqual(self.paths.database.read_bytes(), before)
                self.assertEqual(self.backups(), [])

    def test_locked_database_stops_without_reading_json(self) -> None:
        self.save_winner()
        self.source()
        with closing(sqlite3.connect(self.paths.database)) as connection:
            connection.execute("BEGIN EXCLUSIVE")
            try:
                with patch.object(legacy_import, "decode_legacy_session") as decode:
                    with self.assertRaises(StorageError) as failure:
                        self.load()
                decode.assert_not_called()
                self.assertEqual(failure.exception.kind, StorageFailureKind.LOCKED)
            finally:
                connection.rollback()
        self.assertEqual(self.backups(), [])

    def test_inaccessible_database_does_not_try_the_json_candidate(self) -> None:
        self.source()
        with patch.object(Path, "stat", side_effect=PermissionError()):
            with self.assertRaises(StorageError) as failure:
                self.load()
        self.assertEqual(failure.exception.kind, StorageFailureKind.ACCESS)
        self.assertEqual(failure.exception.path, self.paths.database)
        self.assertEqual(self.backups(), [])

    def test_source_access_and_backup_sync_failure_stop_before_database_creation(
        self,
    ) -> None:
        contents = self.source()
        for target in ("read", "backup"):
            with self.subTest(target=target):
                context = (
                    patch.object(Path, "read_bytes", side_effect=PermissionError())
                    if target == "read"
                    else patch.object(
                        backups.os, "fsync", side_effect=PermissionError()
                    )
                )
                with context, self.assertRaises(StorageError) as failure:
                    self.load()
                self.assertEqual(failure.exception.kind, StorageFailureKind.ACCESS)
                self.assertEqual(failure.exception.path, self.paths.legacy_json)
                self.assertFalse(self.paths.database.exists())
                self.assertEqual(self.backups(), [])
                self.assertEqual(self.paths.legacy_json.read_bytes(), contents)

    def test_partial_snapshot_failure_retains_backup_and_cleans_temporary_database(
        self,
    ) -> None:
        contents = self.source()

        def fail(*args, **kwargs):
            self.assertEqual(self.backups()[0].read_bytes(), contents)
            write_session_rows(*args, **kwargs)
            raise ValueError("Injected after complete owner mapping")

        with patch.object(store_module, "write_session_rows", side_effect=fail):
            with self.assertRaises(StorageError) as failure:
                self.load()
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATA)
        self.assertEqual(failure.exception.path, self.paths.database)
        self.assertFalse(self.paths.database.exists())
        self.assertEqual(self.paths.legacy_json.read_bytes(), contents)
        self.assertEqual(list(self.paths.database.parent.glob(".aiko-*")), [])
        self.assertEqual(self.backups()[0].read_bytes(), contents)

    def test_publication_failure_and_competing_initializer_never_overwrite(
        self,
    ) -> None:
        self.source()
        with patch.object(
            store_module, "publish_database", side_effect=PermissionError()
        ):
            with self.assertRaises(StorageError) as failure:
                self.load()
        self.assertEqual(failure.exception.kind, StorageFailureKind.ACCESS)
        self.assertFalse(self.paths.database.exists())

        def compete(source: Path, destination: Path) -> None:
            with patch.object(store_module, "publish_database", publish_database):
                self.save_winner()
            publish_database(source, destination)

        with patch.object(store_module, "publish_database", side_effect=compete):
            with self.assertRaises(StorageError) as failure:
                self.load()
        self.assertEqual(failure.exception.kind, StorageFailureKind.STALE_REVISION)
        self.assertEqual(self.store.load_session().state.satiety, 12)
        with open_database(self.paths.database) as connection:
            self.assertEqual(
                connection.execute("SELECT count(*) FROM import_provenance").fetchone(),
                (0,),
            )
        self.assertEqual(list(self.paths.database.parent.glob(".aiko-*")), [])

    def test_ordinary_restorer_alone_reconstructs_closed_time_once_after_import(
        self,
    ) -> None:
        self.source(
            json.dumps({
                "version": 1,
                "pet": {"satiety": 75, "updated_at": WALL},
                "settings": {"auto_routine": False},
            }).encode()
        )
        loaded = self.load()
        self.assertEqual(loaded.state.updated_at, WALL)
        self.assertEqual(loaded.state.satiety, 75)
        session = PetSessionRestorer(
            self.store, wall_time=lambda: WALL + 3600
        ).restore()
        self.assertEqual(session.state.updated_at, WALL + 3600)
        self.assertEqual(session.state.lived_seconds, 3600)
        self.assertAlmostEqual(session.state.satiety, 67)
        self.assertEqual(session.revision, SaveRevision(1))
        self.assertEqual(
            encode_pet_state(self.store.load_session().state),
            encode_pet_state(loaded.state),
        )
