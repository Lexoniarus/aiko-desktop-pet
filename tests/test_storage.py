import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session

# Early-epoch timestamps are not universally supported by Windows localtime.
SAMPLE_TIMESTAMP = datetime(2026, 10, 12, 12).astimezone().timestamp()


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = StateStore(Path(self.folder.name) / "nested" / "state.json")

    def test_no_save_starts_fresh(self):
        session_data = self.store.load_session(now=123)
        pet, settings = session_data.state, session_data.settings
        self.assertEqual(pet.updated_at, 123)
        self.assertEqual(pet.satiety, 75)
        self.assertEqual(settings.scale, 1)

    def test_save_and_load_roundtrip(self):
        pet = PetState(
            satiety=88, mood=62, energy=44, sleeping=True, updated_at=SAMPLE_TIMESTAMP
        )
        settings = PetSettings(
            x=155, y=190, scale=2, always_on_top=False, auto_walk=False
        )
        save_test_session(self.store, pet, settings)
        session_data = self.store.load_session(now=SAMPLE_TIMESTAMP)
        loaded, other = session_data.state, session_data.settings
        self.assertEqual(loaded.satiety, 88)
        self.assertTrue(loaded.sleeping)
        self.assertEqual(other, settings)
        self.assertGreater(self.store.load_session().revision.value, 0)
        self.assertEqual(list(self.store.path.parent.glob("*.tmp")), [])

    def test_legacy_save_defaults_preserve_existing_needs(self):
        from datetime import datetime

        timestamp = datetime(2026, 10, 12, 12).astimezone().timestamp()
        self.store.path.parent.mkdir(parents=True, exist_ok=True)
        self.store.paths.legacy_json.write_text(
            json.dumps({
                "version": 1,
                "pet": {
                    "satiety": 42,
                    "mood": 63,
                    "energy": 88,
                    "sleeping": False,
                    "updated_at": timestamp,
                },
                "settings": {"x": 400, "scale": 2, "auto_walk": False},
            })
        )
        session_data = self.store.load_session(now=timestamp)
        pet, settings = session_data.state, session_data.settings
        self.assertEqual((pet.satiety, pet.mood, pet.energy), (42, 63, 88))
        self.assertEqual(settings.x, 400)
        self.assertEqual(settings.scale, 2)
        self.assertFalse(settings.auto_walk)
        self.assertTrue(settings.auto_routine)
        self.assertTrue(settings.follow_cursor)
        self.assertTrue(settings.spontaneous_talk)
        self.assertEqual(pet.meals_today, [])

    def test_malformed_settings_are_rejected(self):
        settings = PetSettings.from_dict({
            "x": True,
            "y": 9999999,
            "scale": 55,
            "always_on_top": False,
            "auto_walk": False,
        })
        self.assertIsNone(settings.x)
        self.assertIsNone(settings.y)
        self.assertEqual(settings.scale, 1)
        self.assertFalse(settings.always_on_top)
        self.assertFalse(settings.auto_walk)

    def test_hardware_monitor_preference_is_optional_and_persisted(self):
        old = PetSettings.from_dict({"scale": 1})
        self.assertTrue(old.observe_computer)
        save_test_session(self.store,
            PetState(updated_at=SAMPLE_TIMESTAMP), PetSettings(observe_computer=False)
        )
        session_data = self.store.load_session(now=SAMPLE_TIMESTAMP)
        _pet, settings = session_data.state, session_data.settings
        self.assertFalse(settings.observe_computer)

    def test_toolbar_location_is_optional_and_survives_restart(self):
        self.assertIsNone(PetSettings.from_dict({"scale": 1}).toolbar_x)
        settings = PetSettings(toolbar_x=77, toolbar_y=130)
        save_test_session(self.store, PetState(updated_at=SAMPLE_TIMESTAMP), settings)
        session_data = self.store.load_session(now=SAMPLE_TIMESTAMP)
        _, loaded = session_data.state, session_data.settings
        self.assertEqual((loaded.toolbar_x, loaded.toolbar_y), (77, 130))
        invalid = PetSettings.from_dict({"toolbar_x": True, "toolbar_y": 70000})
        self.assertIsNone(invalid.toolbar_x)
        self.assertIsNone(invalid.toolbar_y)

    def test_chatter_preference_survives_save_roundtrip(self):
        pet = PetState(updated_at=SAMPLE_TIMESTAMP)
        save_test_session(self.store, pet, PetSettings(spontaneous_talk=False))
        session_data = self.store.load_session(now=SAMPLE_TIMESTAMP)
        _pet, settings = session_data.state, session_data.settings
        self.assertFalse(settings.spontaneous_talk)


if __name__ == "__main__":
    unittest.main()
