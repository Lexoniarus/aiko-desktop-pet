"""No-window SQLite startup, checkpoint failures and autosave cadence."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.storage_contracts import (
    SaveRevision,
    StorageError,
    StorageFailureKind,
)
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.gui import DesktopPet, main
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from tools.persistence_test_support import save_test_session
from tools.pet_test_support import set_test_pet_values


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
            self.store,
            self.state,
            self.settings,
            AdaptiveRoutine(),
            monotonic=lambda: self.clock,
        )

    def test_first_save_and_restart_keep_checkpoint_and_monotonic_revisions(
        self,
    ) -> None:
        self.assertFalse(self.persistence.due(154))
        self.assertTrue(self.persistence.due(155))
        self.assertIsNone(self.persistence.save())
        self.assertEqual(self.store.path.suffix, ".sqlite3")
        self.assertFalse(self.store.paths.legacy_json.exists())
        self.assertEqual(self.persistence.revision, SaveRevision(1))
        restored = PetSessionRestorer(
            self.store, wall_time=lambda: self.stamp
        ).restore()
        self.assertEqual(
            restored.state.capture_checkpoint(), self.state.capture_checkpoint()
        )
        restarted = DesktopPersistence(
            self.store,
            restored.state,
            restored.settings,
            restored.adaptive,
            revision=restored.revision,
        )
        self.assertIsNone(restarted.save())
        self.assertEqual(restarted.revision, SaveRevision(2))

    def test_save_does_not_advance_domain_state(self) -> None:
        set_test_pet_values(self.state, updated_at=self.stamp - 3600)
        with patch.object(self.state, "advance") as progression:
            self.assertIsNone(self.persistence.save())
        progression.assert_not_called()
        self.assertEqual(self.state.updated_at, self.stamp - 3600)

    def test_failed_write_keeps_checkpoint_and_success_time_but_paces_retry(
        self,
    ) -> None:
        self.assertIsNone(self.persistence.save())
        before = self.store.path.read_bytes()
        failure = StorageError(StorageFailureKind.IO, self.store.path, "disk")
        with patch.object(self.store, "save", side_effect=failure):
            self.clock = 200
            self.assertIs(self.persistence.save(), failure)
        self.assertEqual(self.persistence.revision, SaveRevision(1))
        self.assertEqual(self.persistence.last_saved, 100)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertFalse(self.persistence.due(200))
        self.assertTrue(self.persistence.due(255))
        self.assertIsNone(self.persistence.save())
        self.assertEqual(self.persistence.revision, SaveRevision(2))
        self.assertEqual(self.persistence.last_saved, 200)

    def test_stale_desktop_never_adopts_another_sessions_revision_to_retry(
        self,
    ) -> None:
        self.assertIsNone(self.persistence.save())
        save_test_session(
            self.store, PetState(satiety=12, updated_at=self.stamp), self.settings
        )
        before = self.store.path.read_bytes()
        for _ in range(2):
            failure = self.persistence.save()
            assert failure is not None
            self.assertEqual(failure.kind, StorageFailureKind.STALE_REVISION)
            self.assertEqual(self.persistence.revision, SaveRevision(1))
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertEqual(self.store.load_session().state.satiety, 12)

    def test_invalid_startup_stops_before_native_widgets_or_fresh_session(self) -> None:
        self.store.paths.legacy_json.write_bytes(b"broken JSON")
        with patch("aiko_pet.gui.DesktopWindow") as window:
            with self.assertRaises(StorageError):
                DesktopPet(store=self.store)
        window.assert_not_called()
        self.assertFalse(self.store.path.exists())
        self.assertEqual(self.store.paths.legacy_json.read_bytes(), b"broken JSON")

    def test_entrypoint_reports_load_error_and_exits_without_running_desktop(
        self,
    ) -> None:
        failure = StorageError(StorageFailureKind.LOCKED, self.store.path, "locked")
        with (
            patch("aiko_pet.gui.load_env_file"),
            patch("aiko_pet.gui.DesktopPet", side_effect=failure),
            patch("aiko_pet.desktop.startup.messagebox.showerror") as report,
        ):
            with self.assertRaises(SystemExit) as stopped:
                main()
        self.assertEqual(stopped.exception.code, 1)
        report.assert_called_once()
        self.assertIn("nicht gestartet", report.call_args.args[1])
