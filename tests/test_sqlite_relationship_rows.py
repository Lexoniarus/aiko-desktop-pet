"""Retain contact, legacy rewards and named need durations without new effects."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.pet_rows import write_pet_core
from aiko_pet.infrastructure.sqlite.relationship_rows import (
    read_friendship,
    write_friendship,
)
from aiko_pet.pet.friendship_history import (
    CriticalBucket,
    FriendshipHistory,
    RelationshipEvent,
)
from aiko_pet.pet.state import PetState


class SqliteRelationshipRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-relationship-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        with open_database(self.path, initialize=True) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("INSERT INTO save_state VALUES (1, 1, 1780000000, 7200)")
            write_pet_core(connection, PetState(
                updated_at=1780000000, lived_seconds=7200,
            ).capture_checkpoint())
            connection.commit()

    def test_ordered_events_contact_and_compressed_exposure_round_trip(self) -> None:
        history = FriendshipHistory(
            baseline=0, last_contact=7012.3456789, continuous_since=6912.3456789,
            rewards=(RelationshipEvent(7000, "wish", .01),
                     RelationshipEvent(7000, "wish", .02)),
            penalties=(RelationshipEvent(7001, "click", .01),),
            eligible=(("pet", 6999.5), ("talk", 7000.5)),
            critical=(CriticalBucket(3600, (90, 120, 33, 0, 10),
                                     (10, 20, 0, 0, 5), 180),),
        )
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_friendship(connection, history)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            self.assertEqual(read_friendship(connection), history)
            self.assertEqual(connection.execute(
                "SELECT need FROM need_exposure_buckets ORDER BY need"
            ).fetchall(), [(name,) for name in sorted(
                ("satiety", "energy", "fun", "social", "affection")
            )])

    def test_unknown_and_known_empty_histories_remain_distinct(self) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            for history in (FriendshipHistory(), FriendshipHistory(
                baseline=0, continuous_since=0,
            )):
                write_friendship(connection, history)
                self.assertEqual(read_friendship(connection), history)

    def test_partial_need_bucket_is_rejected_without_invented_duration(self) -> None:
        history = FriendshipHistory(baseline=0, critical=(CriticalBucket(3600),))
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_friendship(connection, history)
            connection.execute("DELETE FROM need_exposure_buckets WHERE need = 'fun'")
            with self.assertRaises(ValueError):
                read_friendship(connection)

    def test_replacing_history_removes_retired_rows_and_never_changes_friendship(
        self,
    ) -> None:
        history = FriendshipHistory(baseline=0, critical=(CriticalBucket(3600),))
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            before = connection.execute("SELECT friendship FROM pet_state").fetchone()
            write_friendship(connection, history)
            empty = FriendshipHistory(baseline=0)
            write_friendship(connection, empty)
            self.assertEqual(read_friendship(connection), empty)
            self.assertEqual(connection.execute(
                "SELECT friendship FROM pet_state"
            ).fetchone(), before)


if __name__ == "__main__":
    unittest.main()
