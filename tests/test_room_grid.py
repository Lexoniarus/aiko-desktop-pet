"""Grid migration and depth evidence on isolated, synthetic save data."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.frontend.room_environment import RoomEnvironment
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.room_layout import load_room_layout
from aiko_pet.infrastructure.room_migration import legacy_point
from aiko_pet.infrastructure.sqlite import schema
from aiko_pet.infrastructure.sqlite.session_rows import write_session_rows
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.infrastructure.world_catalog import build_world_definitions
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.mind.object_attention import ObjectAttention
from aiko_pet.pet.mind.object_knowledge import ObjectKnowledge
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint, WorldSurface
from aiko_pet.world.room import RoomGeometry, RoomPoint, RoomSpatialState
from aiko_pet.world.state import WorldState


class RoomGridTests(unittest.TestCase):
    def test_v6_upgrade_preserves_values_ids_and_independent_remembered_place(self):
        folder = self.enterContext(tempfile.TemporaryDirectory())
        path = Path(folder) / "synthetic.sqlite3"
        pet = PetState(satiety=41, updated_at=1800000000, lived_seconds=90000)
        with closing(sqlite3.connect(path)) as db:
            db.execute(f"PRAGMA application_id={schema.APPLICATION_ID}")
            for migration in schema.MIGRATIONS[:6]:
                for statement in migration.statements:
                    db.execute(statement)
                db.execute(
                    "INSERT INTO schema_migrations VALUES (?,?,0)",
                    (migration.version, migration.name),
                )
            db.execute("PRAGMA user_version=6")
            db.execute("INSERT INTO save_state VALUES (1,2,1800000000,90000)")
            write_session_rows(
                db,
                pet.capture_checkpoint(),
                PetSettings(zodiac_sign="leo"),
                adaptive=AdaptiveMemory(),
                social_history=SocialContentHistory(),
                world=None,
                object_memory=None,
                world_recovery_x=0,
            )
            db.execute("INSERT INTO world_state VALUES (1,5100,900,24,9,3)")
            db.execute(
                "INSERT INTO world_objects VALUES "
                "('object_1',1,0,'apple',0,1425,24,24,NULL)"
            )
            db.execute(
                "INSERT INTO world_objects VALUES "
                "('object_2',1,1,'apple',0,4240,24,24,NULL)"
            )
            db.execute(
                "INSERT INTO room_state VALUES (1,'aiko_room',2450,0.8,?)",
                ('[["object_1",0.22],["object_2",0.9]]',),
            )
            db.execute("INSERT INTO object_memory_state VALUES (1,2,3)")
            db.execute(
                "INSERT INTO object_memories VALUES "
                "('memory_1',1,0,'apple','food',930,0,1,2,1,NULL,"
                "'remembered','object_1',0.22)"
            )
            db.commit()
        store = SqliteStateStore(path)
        loaded = store.load_session()
        self.assertEqual(loaded.state.capture_checkpoint(), pet.capture_checkpoint())
        self.assertEqual(loaded.settings.zodiac_sign, "leo")
        assert loaded.world is not None and loaded.world.room is not None
        assert loaded.object_memory is not None
        self.assertEqual(loaded.world.room.geometry_version, 2)
        self.assertEqual(
            [o.instance_id for o in loaded.world.objects], ["object_1", "object_2"]
        )
        known = loaded.object_memory.entries[0]
        historical = legacy_point(930, 0.22)
        self.assertEqual((known.x, known.depth), (historical.x, historical.depth))
        actual = loaded.world.objects[0].position
        assert actual is not None
        self.assertNotEqual(
            (known.x, known.depth), (actual.x, loaded.world.room.depth_for("object_1"))
        )
        self.assertEqual((known.identity, known.instance_id), ("apple", "object_1"))
        self.assertEqual(len(list(path.parent.glob(".*.schema-v6-*.sqlite3"))), 1)
        store.save(
            loaded.state,
            loaded.settings,
            expected_revision=loaded.revision,
            adaptive=loaded.adaptive_memory,
            social_history=loaded.social_history,
            world=loaded.world,
            object_memory=loaded.object_memory,
            world_recovery_x=loaded.world.room.pet.x,
        )
        reopened = store.load_session()
        assert reopened.world is not None
        self.assertEqual(reopened.world.room, loaded.world.room)
        self.assertEqual(reopened.object_memory, loaded.object_memory)
        before = path.read_bytes()
        with patch.object(schema, "SCHEMA_VERSION", 6):
            with self.assertRaises(StorageError):
                store.load_session()
        self.assertEqual(path.read_bytes(), before)

    def test_same_horizontal_position_does_not_make_a_far_object_visible(self):
        geometry = RoomGeometry(load_room_layout())
        world = WorldState(
            WorldSurface(800, 225, 6),
            build_world_definitions(DEFAULT_CATALOG, load_item_catalog()),
        )
        near = world.place_resting("apple", 400, ObjectFootprint(6, 6))
        far = world.place_resting("apple", 400, ObjectFootprint(6, 6))
        world.locate_in_room(
            RoomSpatialState(
                RoomPoint(400, 100),
                (
                    (near.instance_id, 90),
                    (far.instance_id, 500),
                ),
            )
        )
        environment = RoomEnvironment(world, geometry)
        attention = ObjectAttention("survey", (0, -1), (400, 60), 122.5)
        self.assertTrue(environment.sees_instance(near.instance_id, attention))
        self.assertFalse(environment.sees_instance(far.instance_id, attention))
        known = ObjectKnowledge("memory_1", "apple", "food", 400, 0, True, 0, depth=90)
        self.assertFalse(environment.same_place(far.instance_id, known))

    def test_fresh_same_x_sightings_keep_distinct_depth_records(self):
        memory = ObjectMemory()
        first = memory.observe_find(
            ObjectObservation("a", None, None, 400, 0, True, 1, depth=90),
            now=1, record=None, claimed=frozenset(), maximum_distance=12,
        )
        second = memory.observe_find(
            ObjectObservation("b", None, None, 400, 0, True, 1, depth=500),
            now=1, record=None, claimed=frozenset(), maximum_distance=12,
        )
        self.assertNotEqual(first, second)
        self.assertEqual({entry.depth for entry in memory.snapshot()}, {90, 500})
        self.assertTrue(all(entry.identity is None for entry in memory.snapshot()))
