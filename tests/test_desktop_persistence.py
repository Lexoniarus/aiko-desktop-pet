"""Headless persistence tests for unchanged state format and autosave timing."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.adaptive import AdaptiveRoutine
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.domain import PetState
from aiko_pet.storage import PetSettings, StateStore


class FakeReadings:
    def _allow_bedtime(self) -> bool | None:
        return None

    def _allow_nap(self) -> bool:
        return False

    def _interrupt_nap(self) -> bool:
        return False

    def _live_effort(self) -> float | None:
        return None


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
            AdaptiveRoutine(), FakeReadings(),
            monotonic=lambda: self.clock,
            wall_time=lambda: self.stamp,
        )

    def test_writes_existing_schema_only_after_bound_time(self) -> None:
        self.assertFalse(self.persistence.due(154))
        self.assertTrue(self.persistence.due(155))
        self.assertIsNone(self.persistence.save())
        loaded, settings = self.store.load(now=self.stamp)
        self.assertEqual(loaded.to_dict(), self.state.to_dict())
        self.assertEqual(settings.to_dict(), self.settings.to_dict())

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
