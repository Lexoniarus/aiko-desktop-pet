"""Joint Pet/World/memory saves retain subjective history across closed time."""

import tempfile
import unittest
from pathlib import Path

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.object_consumption import ObjectConsumption
from aiko_pet.application.session import PetSessionRestorer, WorldSessionSnapshot
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.storage_contracts import StorageError
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint, ObjectState, WorldSurface
from aiko_pet.world.state import WorldState
from tools.persistence_test_support import save_test_session


class ObjectMemoryPersistenceTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = StateStore(Path(folder.name) / "state.json")
        self.world = WorldState(WorldSurface(2000, 600), build_consumable_definitions(
            DEFAULT_CATALOG, load_item_catalog(),
        ))
        self.item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        self.memory = ObjectMemory()
        self.memory.update((ObjectObservation(
            self.item.instance_id, "apple", "food", 100, 0, True, 1000,
        ),), now=1000)
        self.memory.mark_assessed(self.item.instance_id)
        self.memory.note_placement(self.item.instance_id, x=100, height=0,
                                   now=1000, deferred=True)
        self.state = PetState(satiety=80, updated_at=1_800_000_000)
        self.settings = PetSettings(auto_routine=False)

    def save(self):
        save_test_session(
            self.store, self.state, self.settings, world=self.world.snapshot(),
                        object_memory=self.memory.export(now=1005))

    def test_joint_save_restores_facts_without_aging_during_closed_time(self):
        self.save()
        restored = PetSessionRestorer(
            self.store, wall_time=lambda: self.state.updated_at + 3600,
        ).restore()
        self.assertEqual(restored.object_memory, self.memory.export(now=1005))
        self.assertLess(restored.state.satiety, self.state.satiety)
        known = ObjectMemory(restored.object_memory).snapshot()[0]
        self.assertEqual((known.observed_at, known.assessed, known.disposition),
                         (-5, True, "deferred"))

    def test_hidden_move_or_removal_is_not_reconciled_from_saved_world(self):
        for removed in (False, True):
            with self.subTest(removed=removed):
                current = self.world.get(self.item.instance_id)
                if removed:
                    self.world.remove(current.instance_id,
                                       expected_revision=current.revision)
                else:
                    self.world.move_resting(current.instance_id, 1800,
                                             expected_revision=current.revision)
                self.save()
                loaded = self.store.load_session()
                known = ObjectMemory(loaded.object_memory).snapshot()[0]
                self.assertEqual((known.x, known.identity), (100, "apple"))
                assert loaded.world is not None
                if removed:
                    self.assertEqual(loaded.world.objects, ())
                else:
                    assert loaded.world.objects[0].position is not None
                    self.assertNotEqual(loaded.world.objects[0].position.x, known.x)

    def test_world_without_memory_does_not_grant_catalog_knowledge(self):
        save_test_session(
            self.store, self.state, self.settings, world=self.world.snapshot())
        loaded = self.store.load_session()
        self.assertIsNone(loaded.object_memory)
        self.assertEqual(ObjectMemory(loaded.object_memory).snapshot(), ())

    def test_memory_requires_world_in_the_same_durable_snapshot(self):
        with self.assertRaises(StorageError):
            save_test_session(self.store, self.state, self.settings,
                            object_memory=self.memory.export(now=1005))
        self.assertFalse(self.store.path.exists())

    def test_held_recovery_does_not_invent_a_subjectively_observed_ground_pose(self):
        self.world.collect_resting(self.item.instance_id, expected_revision=0)
        self.memory.note_acquired(self.item.instance_id, now=1001)
        save_test_session(
            self.store, self.state, self.settings, world=self.world.snapshot(),
                        world_recovery_x=800,
                        object_memory=self.memory.export(now=1005))
        loaded = self.store.load_session()
        assert loaded.world is not None
        self.assertEqual(loaded.world.objects[0].state, ObjectState.RESTING)
        assert loaded.world.objects[0].position is not None
        self.assertEqual(loaded.world.objects[0].position.x, 800)
        known = ObjectMemory(loaded.object_memory).snapshot()[0]
        self.assertEqual(known.x, 100)
        self.assertFalse(known.resting)
        self.assertTrue(known.assessed)
        self.assertIsNone(known.disposition)

    def test_desktop_writer_captures_world_and_cognition_in_one_save(self):
        persistence = DesktopPersistence(
            self.store, self.state, self.settings, AdaptiveRoutine(),
            monotonic=lambda: 1,
        )
        persistence.attach_world(lambda: WorldSessionSnapshot(
            self.world.snapshot(), self.memory.export(now=1005), 500,
        ))
        self.assertIsNone(persistence.save())
        self.assertEqual(self.store.load_session().object_memory,
                         self.memory.export(now=1005))

    def test_save_at_consumption_commit_has_no_portion_or_memory_target(self):
        self.world.collect_resting(self.item.instance_id, expected_revision=0)
        self.memory.note_acquired(self.item.instance_id, now=1001)
        use_case = ObjectConsumption(
            self.state, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0), memory=self.memory,
        )
        outcome = use_case.commit(
            self.world, "test", self.item.instance_id, ConsumptionOrigin.AUTONOMOUS,
            SessionInputs(self.state.updated_at, 1, False, None, False, False, None),
            memory_id=self.item.instance_id,
        )
        self.assertTrue(outcome.accepted)
        # Saving precedes the remaining visible clip and final bubble.
        self.save()
        loaded = self.store.load_session()
        assert loaded.world is not None
        self.assertEqual(loaded.world.objects, ())
        self.assertEqual(ObjectMemory(loaded.object_memory).snapshot(), ())
        self.assertGreater(loaded.state.satiety, 80)
