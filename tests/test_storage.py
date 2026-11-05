import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import set_test_pet_values

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
            x=155, y=190, scale=2, always_on_top=False, auto_walk=False,
            auto_routine=False, follow_cursor=False, spontaneous_talk=False,
            observe_computer=False, learn_rhythm=False, online_social=True,
            toolbar_x=77, toolbar_y=130,
        )
        save_test_session(self.store, pet, settings)
        session_data = self.store.load_session(now=SAMPLE_TIMESTAMP)
        loaded, other = session_data.state, session_data.settings
        self.assertEqual(loaded.capture_checkpoint(), pet.capture_checkpoint())
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
                    "social": 24, "friendship": 54,
                    "care_last_rewards": {"sleep": timestamp - 400},
                },
                "settings": {"x": 400, "scale": 2, "auto_walk": False,
                             "toolbar_x": 120, "toolbar_y": 70},
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
        self.assertEqual((pet.social, pet.affection, pet.friendship), (24, 75, 54))
        self.assertIn("sleep", pet.care_last_rewards)
        self.assertEqual((settings.toolbar_x, settings.toolbar_y), (120, 70))
        save_test_session(self.store, pet, settings)
        again = self.store.load_session(now=timestamp).state
        self.assertEqual(again.capture_checkpoint(), pet.capture_checkpoint())

    def test_new_relationship_metadata_survives_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "pet.json")
            state = PetState(updated_at=SAMPLE_TIMESTAMP, affection=35)
            state.interact("pet", now=SAMPLE_TIMESTAMP)
            set_test_pet_values(state, social=35)
            state.interact("talk", now=SAMPLE_TIMESTAMP + 1)
            save_test_session(store, state, PetSettings())
            session_data = store.load_session(now=SAMPLE_TIMESTAMP + 1)
            restored, _ = session_data.state, session_data.settings
            self.assertEqual(restored.care_types_today, [])
            self.assertEqual(
                set(dict(restored.friendship_history.eligible)), set()
            )
            self.assertEqual(restored.friendship_history, state.friendship_history)
            self.assertEqual(restored.care_last_rewards, state.care_last_rewards)
            self.assertEqual(restored.friendship, state.friendship)
            self.assertAlmostEqual(restored.affection, state.affection, places=2)


if __name__ == "__main__":
    unittest.main()
