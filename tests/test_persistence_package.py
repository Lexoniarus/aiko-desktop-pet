"""Canonical SQLite repository, legacy aliases and relative save location."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session

class PersistencePackageTests(unittest.TestCase):
    def test_canonical_store_saves_sqlite_without_creating_legacy_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "saved.json")
            state = PetState(satiety=47, updated_at=1_780_000_000)
            settings = PetSettings(auto_routine=False, scale=2)
            save_test_session(store, state, settings)
            self.assertEqual(store.path.suffix, ".sqlite3")
            self.assertFalse(store.paths.legacy_json.exists())
            session_data = store.load_session(now=1_780_000_000)
            loaded, other = session_data.state, session_data.settings
            self.assertEqual(encode_pet_state(loaded), encode_pet_state(state))
            self.assertEqual(other, settings)


if __name__ == "__main__":
    unittest.main()
