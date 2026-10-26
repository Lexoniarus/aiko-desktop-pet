"""Complete SQLite transactions reject stale writers and incomplete first saves."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from test_horoscope import NOW
from test_sqlite_adaptive_rows import profile
from test_sqlite_care_evidence import complete_emotional_state
from test_sqlite_food_handovers import handover_state
from test_sqlite_horoscope import admitted_day
from test_sqlite_social_rows import social_history

from aiko_pet.application.horoscope_models import HoroscopeHistory
from aiko_pet.application.session import SavedPetReader, SavedPetWriter
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.storage_contracts import (
    SaveRevision,
    StorageError,
    StorageFailureKind,
)
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.sqlite import store as store_module
from aiko_pet.infrastructure.sqlite.publication import publish_database
from aiko_pet.infrastructure.sqlite.session_rows import write_session_rows
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.infrastructure.world_catalog import build_world_definitions
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.friendship_history import FriendshipHistory
from aiko_pet.pet.mind.object_knowledge import (
    ObjectMemorySnapshot,
    SavedObjectKnowledge,
)
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint, WorldSurface
from aiko_pet.world.state import WorldState


class SqliteStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-sqlite-store-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "save.sqlite3"
        self.store = SqliteStateStore(self.path)
        self.pet = PetState(
            updated_at=1800000000,
            lived_seconds=100000,
            relationship=FriendshipHistory(baseline=0, last_contact=99900),
            moodlets=complete_emotional_state(),
            wishes=handover_state(),
        )
        self.settings = PetSettings(x=-120, scale=2, zodiac_sign="leo")
        self.adaptive = profile()
        self.history = social_history()
        definitions = build_world_definitions(DEFAULT_CATALOG, load_item_catalog())
        world = WorldState(WorldSurface(800, 600, 96), definitions)
        item = world.place_resting("apple", 100, ObjectFootprint(8, 8))
        book = world.place_resting("horoscope_book", 200, ObjectFootprint(64, 48))
        self.horoscope = HoroscopeHistory((
            replace(admitted_day(), book_instance_id=book.instance_id),
        ))
        self.world = world.snapshot()
        self.memory = ObjectMemorySnapshot(
            (
                SavedObjectKnowledge(
                    "memory_1",
                    "apple",
                    "food",
                    100,
                    0,
                    True,
                    80,
                    True,
                    None,
                    instance_id=item.instance_id,
                ),
            ),
            2,
        )

    def save(
        self,
        revision: SaveRevision,
        *,
        store: SqliteStateStore | None = None,
        pet: PetState | None = None,
    ) -> SaveRevision:
        writer: SavedPetWriter = store or self.store
        return writer.save(
            pet or self.pet,
            self.settings,
            expected_revision=revision,
            adaptive=self.adaptive,
            social_history=self.history,
            horoscope=self.horoscope,
            world=self.world,
            object_memory=self.memory,
        )

    def changed_pet(self) -> PetState:
        pet = deepcopy(self.pet)
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), satiety=12))
        return pet

    def test_active_reading_cannot_reference_missing_or_edible_object(self) -> None:
        self.pet = PetState(updated_at=NOW)
        for book_id in ("object_1", "object_99"):
            with self.subTest(book_id=book_id):
                self.horoscope = HoroscopeHistory((
                    replace(admitted_day(), book_instance_id=book_id),
                ))
                with self.assertRaises(StorageError):
                    self.save(SaveRevision())
                self.assertFalse(self.path.exists())

    def test_loading_rejects_reading_bound_to_an_edible_object(self) -> None:
        self.save(SaveRevision())
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute(
                "UPDATE local_horoscope_days SET book_id='object_1'"
            )
            connection.commit()
        with self.assertRaises(StorageError):
            self.store.load_session()

    def test_retired_book_history_survives_an_earlier_pet_clock(self) -> None:
        day = self.horoscope.days[0]
        assert day.reading is not None and day.book_instance_id is not None
        self.horoscope = HoroscopeHistory((replace(
            day, completed=True, index=len(day.reading.reaction.beats),
            first_put_down_at=NOW,
        ),))
        world = WorldState(self.world.surface, self.world.definitions)
        world.restore_snapshot(self.world)
        book = world.get(day.book_instance_id)
        world.set_book_expiry(book.instance_id, NOW + 3600)
        world.expire_books(NOW + 3600)
        self.world = world.snapshot()
        self.pet = PetState(updated_at=NOW)
        self.save(SaveRevision())
        restored = self.store.load_session()
        self.assertEqual(restored.horoscope, self.horoscope)
        assert restored.world is not None
        self.assertNotIn(book.instance_id,
                         {item.instance_id for item in restored.world.objects})

    def test_fresh_load_and_complete_round_trip_never_advance_or_mutate_inputs(
        self,
    ) -> None:
        reader: SavedPetReader = self.store
        fresh = reader.load_session(now=1800000000)
        self.assertFalse(self.path.exists())
        self.assertFalse(fresh.restored_from_save)
        self.assertEqual(fresh.revision, SaveRevision())
        before = self.pet.capture_checkpoint()
        revision = self.save(fresh.revision)
        self.assertEqual(revision, SaveRevision(1))
        with patch.object(
            PetState, "advance", side_effect=AssertionError("No simulation")
        ):
            loaded = reader.load_session(now=1800259200)
        self.assertEqual(loaded.state.capture_checkpoint(), before)
        self.assertEqual(self.pet.capture_checkpoint(), before)
        self.assertEqual(
            (loaded.settings, loaded.adaptive_memory, loaded.social_history),
            (self.settings, self.adaptive, self.history),
        )
        self.assertEqual(
            (loaded.world, loaded.object_memory), (self.world, self.memory)
        )
        self.assertEqual(loaded.horoscope, self.horoscope)
        self.assertEqual(loaded.revision, revision)
        self.assertEqual(self.save(revision), SaveRevision(2))

    def test_stale_session_cannot_overwrite_a_newer_committed_checkpoint(self) -> None:
        old = self.save(SaveRevision())
        other = SqliteStateStore(self.path)
        current = self.save(old, store=other, pet=self.changed_pet())
        before = self.path.read_bytes()
        with self.assertRaises(StorageError) as failure:
            self.save(old)
        self.assertEqual(failure.exception.kind, StorageFailureKind.STALE_REVISION)
        self.assertEqual(old, SaveRevision(1))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(other.load_session().revision, current)
        self.assertEqual(other.load_session().state.satiety, 12)

    def test_partial_write_failure_keeps_all_owners_and_expected_revision(self) -> None:
        revision = self.save(SaveRevision())

        def fail(*args, **kwargs):
            write_session_rows(*args, **kwargs)
            raise ValueError("Injected failure after mapped writes")

        with patch.object(store_module, "write_session_rows", side_effect=fail):
            with self.assertRaises(StorageError) as failure:
                self.save(revision, pet=self.changed_pet())
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATA)
        self.assertEqual(failure.exception.path, self.path)
        loaded = self.store.load_session()
        self.assertEqual(loaded.horoscope, self.horoscope)
        self.assertEqual(loaded.revision, revision)
        self.assertEqual(
            loaded.state.capture_checkpoint(), self.pet.capture_checkpoint()
        )
        self.assertEqual(
            (loaded.world, loaded.object_memory), (self.world, self.memory)
        )
        self.assertEqual(self.save(revision, pet=self.changed_pet()), SaveRevision(2))

    def test_reader_sees_old_complete_snapshot_while_another_write_is_uncommitted(
        self,
    ) -> None:
        revision = self.save(SaveRevision())
        observed = []

        def inspect(connection, *args, **kwargs):
            connection.execute("UPDATE pet_state SET satiety = 99")
            observed.append(SqliteStateStore(self.path).load_session())
            write_session_rows(connection, *args, **kwargs)

        with patch.object(store_module, "write_session_rows", side_effect=inspect):
            self.save(revision, pet=self.changed_pet())
        self.assertEqual(len(observed), 1)
        self.assertEqual(observed[0].revision, revision)
        self.assertEqual(
            observed[0].state.capture_checkpoint(), self.pet.capture_checkpoint()
        )
        self.assertEqual(self.store.load_session().state.satiety, 12)

    def test_database_lock_is_reported_without_waiting_or_consuming_revision(
        self,
    ) -> None:
        revision = self.save(SaveRevision())
        with closing(sqlite3.connect(self.path)) as blocker:
            blocker.execute("BEGIN EXCLUSIVE")
            try:
                with self.assertRaises(StorageError) as failure:
                    self.save(revision)
                self.assertEqual(failure.exception.kind, StorageFailureKind.LOCKED)
            finally:
                blocker.rollback()
        self.assertEqual(self.store.load_session().revision, revision)

    def test_two_first_savers_never_replace_the_winning_publication(self) -> None:
        entered = False

        def compete(source: Path, destination: Path) -> None:
            nonlocal entered
            if not entered:
                entered = True
                self.save(
                    SaveRevision(),
                    store=SqliteStateStore(self.path),
                    pet=self.changed_pet(),
                )
            publish_database(source, destination)

        with patch.object(store_module, "publish_database", side_effect=compete):
            with self.assertRaises(StorageError) as failure:
                self.save(SaveRevision())
        self.assertEqual(failure.exception.kind, StorageFailureKind.STALE_REVISION)
        loaded = self.store.load_session()
        self.assertEqual((loaded.state.satiety, loaded.revision), (12, SaveRevision(1)))
        self.assertEqual(list(self.path.parent.glob(".aiko-*")), [])

    def test_failed_first_write_and_access_failure_do_not_publish_a_partial_save(
        self,
    ) -> None:
        invalid = self.changed_pet()
        invalid.restore_checkpoint(
            replace(invalid.capture_checkpoint(), satiety=float("nan"))
        )
        with self.assertRaises(StorageError) as failure:
            self.save(SaveRevision(), pet=invalid)
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATA)
        self.assertEqual(failure.exception.path, self.path)
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.path.parent.glob(".aiko-*")), [])
        with patch.object(Path, "mkdir", side_effect=PermissionError("Denied")):
            with self.assertRaises(StorageError) as failure:
                self.save(SaveRevision())
        self.assertEqual(failure.exception.kind, StorageFailureKind.ACCESS)
        self.assertFalse(self.path.exists())

    def test_missing_expected_save_and_foreign_file_are_not_replaced(self) -> None:
        revision = self.save(SaveRevision())
        self.path.unlink()
        with self.assertRaises(StorageError) as failure:
            self.save(revision)
        self.assertEqual(failure.exception.kind, StorageFailureKind.STALE_REVISION)
        self.assertFalse(self.path.exists())
        self.path.write_bytes(b"Not an Aiko database")
        with self.assertRaises(StorageError) as failure:
            self.save(SaveRevision())
        self.assertEqual(failure.exception.kind, StorageFailureKind.INVALID_DATABASE)
        self.assertEqual(self.path.read_bytes(), b"Not an Aiko database")


if __name__ == "__main__":
    unittest.main()
