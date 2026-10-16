"""Smoke profiles are isolated and explicit restart never reseeds state."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.world.contracts import ObjectFootprint, WorldSurface
from aiko_pet.world.state import WorldState
from tools.world_smoke import prepare_session


class WorldSmokeTests(unittest.TestCase):
    def test_curious_profile_reproduces_the_reported_need_levels(self):
        with tempfile.TemporaryDirectory() as folder:
            store = prepare_session(Path(folder) / "state.json", scenario="curious")
            session = store.load_session()
            self.assertEqual(session.state.satiety, 76)
            self.assertEqual(session.state.energy, 60)
            self.assertFalse(session.settings.spontaneous_talk)

    def test_hungry_and_full_profiles_have_different_needs_without_random_walk(self):
        with tempfile.TemporaryDirectory() as folder:
            for scenario, level in (("hungry", 55), ("full", 100)):
                store = prepare_session(Path(folder) / scenario / "state.json",
                                        scenario=scenario)
                session = store.load_session()
                self.assertEqual(session.state.satiety, level)
                self.assertFalse(session.settings.auto_walk)
                self.assertFalse(session.settings.auto_routine)
                prepare_session(store.path,
                                scenario="full" if level == 55 else "hungry")
                self.assertEqual(store.load_session().state.satiety, level)

    def test_normal_save_path_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "normal.json"
            with patch("tools.world_smoke.default_save_path", return_value=path):
                with self.assertRaises(ValueError):
                    prepare_session(path, scenario="hungry")
            self.assertFalse(path.exists())

    def test_explicit_need_override_preserves_known_world_portion_and_memory(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "state.json"
            store = prepare_session(path, scenario="full")
            loaded = store.load_session()
            world = WorldState(WorldSurface(800, 600), build_consumable_definitions(
                DEFAULT_CATALOG, load_item_catalog(),
            ))
            item = world.place_resting("energy_drink", 100, ObjectFootprint(12, 12))
            memory = ObjectMemory()
            memory.update((ObjectObservation(
                item.instance_id, "energy_drink", "drink", 100, 0, True, 0,
            ),), now=0)
            memory.mark_assessed(item.instance_id)
            memory.note_placement(item.instance_id, x=100, height=0,
                                   now=0, deferred=True)
            store.save(loaded.state, loaded.settings, world=world.snapshot(),
                        object_memory=memory.export(now=20))
            before = store.load_session()
            prepare_session(path, scenario="full", needs="hungry")
            after = store.load_session()
            self.assertEqual((after.state.satiety, after.state.energy), (55, 55))
            self.assertEqual(after.world, before.world)
            self.assertEqual(after.object_memory, before.object_memory)
            self.assertEqual(after.state.friendship, before.state.friendship)

    def test_need_override_still_cannot_write_the_normal_save(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "normal.json"
            with patch("tools.world_smoke.default_save_path", return_value=path):
                with self.assertRaises(ValueError):
                    prepare_session(path, scenario="full", needs="hungry")
            self.assertFalse(path.exists())
