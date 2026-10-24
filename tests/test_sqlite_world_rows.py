"""Ground stock and historical subjective knowledge remain separate in SQL."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.infrastructure.sqlite.connection import open_database
from aiko_pet.infrastructure.sqlite.pet_rows import read_pet_core, write_pet_core
from aiko_pet.infrastructure.sqlite.relationship_rows import (
    read_friendship,
    write_friendship,
)
from aiko_pet.infrastructure.sqlite.settings_rows import read_settings, write_settings
from aiko_pet.infrastructure.sqlite.world_rows import (
    read_world_memory,
    write_world_memory,
)
from aiko_pet.pet.mind.object_knowledge import (
    ObjectMemorySnapshot,
    SavedObjectKnowledge,
)
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldObjectSnapshot,
    WorldPosition,
    WorldSnapshot,
    WorldSurface,
)


class SqliteWorldRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-world-rows-")
        self.addCleanup(folder.cleanup)
        self.path = Path(folder.name) / "fixture.sqlite3"
        self.definitions = (
            ObjectDefinition(
                "apple", "apple", "apple", frozenset({ObjectInteraction.EAT})
            ),
        )
        footprint = ObjectFootprint(8, 8)
        self.world = WorldSnapshot(
            WorldSurface(800, 600, 96),
            17,
            self.definitions,
            (
                WorldObjectSnapshot(
                    "object_1",
                    "apple",
                    2,
                    ObjectState.USER_HELD,
                    WorldPosition(50, 300),
                    footprint,
                ),
                WorldObjectSnapshot(
                    "object_2", "apple", 3, ObjectState.PET_HELD, None, footprint
                ),
                WorldObjectSnapshot(
                    "object_3", "apple", 4, ObjectState.CONSUMED, None, footprint
                ),
            ),
            4,
        )
        self.memory = ObjectMemorySnapshot(
            (
                SavedObjectKnowledge(
                    "memory_1",
                    "apple",
                    "food",
                    300,
                    0,
                    True,
                    9876.54321,
                    True,
                    None,
                    "missing",
                    (),
                    "object_3",
                ),
                SavedObjectKnowledge(
                    "memory_2",
                    "apple",
                    "food",
                    400,
                    0,
                    True,
                    120.123456789,
                    True,
                    "deferred",
                    "remembered",
                    ("memory_1",),
                ),
                SavedObjectKnowledge(
                    "memory_3", None, None, 96, 0, True, 10, False, None
                ),
            ),
            4,
        )
        with open_database(self.path, initialize=True) as connection:
            connection.execute("INSERT INTO save_state VALUES (1, 1, 1780000000, 7200)")

    def test_transient_stock_recovers_safely_without_changing_subjective_evidence(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_world_memory(connection, self.world, self.memory, recovery_x=250)
            connection.commit()
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            world, memory = read_world_memory(connection, self.definitions)
            assert world is not None and memory is not None
            self.assertEqual(world.surface, self.world.surface)
            self.assertEqual((world.revision, world.next_instance_id), (17, 4))
            self.assertEqual(
                [
                    (item.instance_id, item.position, item.revision)
                    for item in world.objects
                ],
                [
                    ("object_1", WorldPosition(96, 0), 3),
                    ("object_2", WorldPosition(250, 0), 4),
                ],
            )
            self.assertTrue(
                all(
                    item.state == ObjectState.RESTING and item.motion is None
                    for item in world.objects
                )
            )
            self.assertEqual(memory, self.memory)
            self.assertEqual(memory.entries[0].instance_id, "object_3")
            self.assertIsNone(memory.entries[2].identity)

    def test_absent_and_initialized_empty_world_and_memory_remain_distinct(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            self.assertEqual(
                read_world_memory(connection, self.definitions), (None, None)
            )
            empty = replace(self.world, objects=())
            write_world_memory(connection, empty, None, recovery_x=250)
            self.assertEqual(
                read_world_memory(connection, self.definitions), (empty, None)
            )
            write_world_memory(
                connection, empty, ObjectMemorySnapshot(), recovery_x=250
            )
            self.assertEqual(
                read_world_memory(connection, self.definitions),
                (empty, ObjectMemorySnapshot()),
            )
            write_world_memory(connection, None, None, recovery_x=250)
            self.assertEqual(
                read_world_memory(connection, self.definitions), (None, None)
            )

    def test_forgetting_a_memory_removes_edges_without_deleting_other_knowledge(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_world_memory(connection, self.world, self.memory, recovery_x=250)
            connection.execute("DELETE FROM object_memories WHERE token = 'memory_1'")
            world, memory = read_world_memory(connection, self.definitions)
            assert world is not None and memory is not None
            self.assertEqual(
                [entry.token for entry in memory.entries], ["memory_2", "memory_3"]
            )
            self.assertEqual(memory.entries[0].possible_sources, ())
            self.assertEqual(len(world.objects), 2)

    def test_invalid_pair_or_associations_cannot_replace_the_saved_values(self) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_world_memory(connection, self.world, self.memory, recovery_x=250)
            before = read_world_memory(connection, self.definitions)
            with self.assertRaises(ValueError):
                write_world_memory(connection, None, self.memory, recovery_x=250)
            invalid = replace(
                self.memory,
                entries=(
                    self.memory.entries[0],
                    replace(self.memory.entries[1], possible_sources=("memory_2",)),
                ),
            )
            with self.assertRaises(ValueError):
                write_world_memory(connection, self.world, invalid, recovery_x=250)
            self.assertEqual(read_world_memory(connection, self.definitions), before)

    def test_wrong_allocation_provenance_is_not_accepted_as_subjective_evidence(
        self,
    ) -> None:
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_world_memory(connection, self.world, self.memory, recovery_x=250)
            connection.execute("UPDATE object_memory_state SET world_next_id = 5")
            with self.assertRaises(ValueError):
                read_world_memory(connection, self.definitions)

    def test_mapped_owners_share_one_commit_and_roll_back_together(self) -> None:
        snapshot = PetState(
            updated_at=1780000000, lived_seconds=7200
        ).capture_checkpoint()
        settings = PetSettings(x=-200, scale=2, online_social=True)
        with open_database(self.path) as connection:
            connection.execute("BEGIN IMMEDIATE")
            write_pet_core(connection, snapshot)
            write_friendship(connection, snapshot.relationship)
            write_settings(connection, settings)
            write_world_memory(connection, self.world, self.memory, recovery_x=250)
            original_pair = read_world_memory(connection, self.definitions)
            connection.commit()
        with self.assertRaises(StorageError):
            with open_database(self.path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE save_state SET revision = 2, "
                    "updated_at = 1780000030, lived_seconds = 7230"
                )
                write_pet_core(
                    connection,
                    replace(
                        snapshot, mood=1, updated_at=1780000030, lived_seconds=7230
                    ),
                )
                write_world_memory(connection, None, None, recovery_x=250)
                connection.execute("UPDATE app_settings SET scale = 3")
        with open_database(self.path) as connection:
            connection.execute("BEGIN")
            restored = read_pet_core(connection, snapshot)
            restored = replace(restored, relationship=read_friendship(connection))
            self.assertEqual(restored, snapshot)
            self.assertEqual(read_settings(connection), settings)
            self.assertEqual(
                read_world_memory(connection, self.definitions), original_pair
            )
            self.assertEqual(
                connection.execute("SELECT revision FROM save_state").fetchone(), (1,)
            )


if __name__ == "__main__":
    unittest.main()
