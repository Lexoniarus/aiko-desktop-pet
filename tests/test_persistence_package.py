"""Canonical SQLite repository, legacy aliases and relative save location."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import (
    StateStore,
    default_save_path,
)
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session

ROOT = Path(__file__).resolve().parents[1]


class PersistencePackageTests(unittest.TestCase):
    def test_relative_save_override_is_still_based_on_repository_root(self) -> None:
        with patch.dict(os.environ, {"AIKO_SAVE_PATH": "test-saves/local.json"}):
            self.assertEqual(
                default_save_path(), ROOT / "test-saves" / "local.sqlite3",
            )

    def test_absolute_save_override_does_not_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            expected = Path(directory) / "nested" / "saved.json"
            with patch.dict(os.environ, {"AIKO_SAVE_PATH": str(expected)}):
                self.assertEqual(default_save_path(), expected.with_suffix(".sqlite3"))

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
