"""Canonical JSON repository, stable defaults and relative save location."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import (
    SCHEMA_VERSION, StateStore, default_save_path,
)
from aiko_pet.pet.state import PetState
from aiko_pet.storage import (
    SCHEMA_VERSION as LegacyVersion,
    PetSettings as LegacySettings,
    StateStore as LegacyStore,
    default_save_path as legacy_save_path,
)

ROOT = Path(__file__).resolve().parents[1]


class PersistencePackageTests(unittest.TestCase):
    def test_legacy_repository_imports_preserve_exact_types(self) -> None:
        self.assertIs(LegacyStore, StateStore)
        self.assertIs(LegacySettings, PetSettings)
        self.assertIs(legacy_save_path, default_save_path)
        self.assertEqual(LegacyVersion, SCHEMA_VERSION)
        self.assertEqual(SCHEMA_VERSION, 1)

    def test_relative_save_override_is_still_based_on_repository_root(self) -> None:
        with patch.dict(os.environ, {"AIKO_SAVE_PATH": "test-saves/local.json"}):
            self.assertEqual(
                default_save_path(), ROOT / "test-saves" / "local.json",
            )
            self.assertEqual(legacy_save_path(), default_save_path())

    def test_absolute_save_override_does_not_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            expected = Path(directory) / "nested" / "saved.json"
            with patch.dict(os.environ, {"AIKO_SAVE_PATH": str(expected)}):
                self.assertEqual(default_save_path(), expected)

    def test_new_canonical_store_writes_same_json_schema(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = StateStore(Path(directory) / "saved.json")
            state = PetState(satiety=47, updated_at=1_780_000_000)
            settings = PetSettings(auto_routine=False, scale=2)
            store.save(state, settings)
            saved = json.loads(store.path.read_text(encoding="utf-8"))
            self.assertEqual(saved["version"], 1)
            self.assertEqual(saved["pet"], state.to_dict())
            self.assertEqual(saved["settings"], settings.to_dict())
            loaded, other = store.load(now=1_780_000_000)
            self.assertEqual(loaded.to_dict(), state.to_dict())
            self.assertEqual(other, settings)


if __name__ == "__main__":
    unittest.main()
