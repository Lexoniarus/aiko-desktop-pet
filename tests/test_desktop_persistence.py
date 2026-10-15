"""Headless persistence tests for unchanged state format and autosave timing."""

from __future__ import annotations

from aiko_pet.infrastructure.pet_codec import encode_pet_state

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.pet.state import PetState
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.persistence import StateStore


class DesktopPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = StateStore(Path(folder.name) / "state.json")
        self.stamp = 1_781_000_000.0
        self.state = PetState(updated_at=self.stamp)
        self.settings = PetSettings(auto_routine=False)
        self.clock = 100.0
        self.persistence = DesktopPersistence(
            self.store, self.state, self.settings,
            AdaptiveRoutine(),
            monotonic=lambda: self.clock,
        )

    def test_writes_existing_schema_only_after_bound_time(self) -> None:
        self.assertFalse(self.persistence.due(154))
        self.assertTrue(self.persistence.due(155))
        self.assertIsNone(self.persistence.save())
        saved = json.loads(self.store.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["version"], 1)
        self.assertEqual(saved["pet"], encode_pet_state(self.state))
        self.assertEqual(saved["settings"], self.settings.to_dict())

    def test_save_does_not_advance_domain_state(self) -> None:
        self.state.updated_at = self.stamp - 3600
        with patch.object(self.state, "advance") as progression:
            self.assertIsNone(self.persistence.save())
        progression.assert_not_called()
        self.assertEqual(self.state.updated_at, self.stamp - 3600)

    def test_failure_returns_error_but_retains_original_timer_semantics(self) -> None:
        with patch.object(self.store, "save", side_effect=OSError("disk")):
            self.clock = 200
            error = self.persistence.save()
        self.assertIsInstance(error, OSError)
        self.assertEqual(self.persistence.last_saved, 200)
        self.assertFalse(self.persistence.due(200))
        self.assertTrue(self.persistence.due(255))


if __name__ == "__main__":
    unittest.main()
