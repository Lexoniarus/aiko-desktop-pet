"""Storage identity/failure values stay independent of backend exception types."""

import unittest
from pathlib import Path

from aiko_pet.application.storage_contracts import (
    MAX_SAVE_REVISION,
    SaveRevision,
    StorageError,
    StorageFailureKind,
)


class StorageContractTests(unittest.TestCase):
    def test_revision_distinguishes_fresh_and_persisted_checkpoints(self) -> None:
        self.assertEqual(SaveRevision().value, 0)
        self.assertEqual(SaveRevision(MAX_SAVE_REVISION).value, MAX_SAVE_REVISION)
        for invalid in (-1, MAX_SAVE_REVISION + 1, True):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                SaveRevision(invalid)

    def test_failure_exposes_backend_independent_reason_and_affected_path(self) -> None:
        path = Path("fixture.sqlite3")
        error = StorageError(StorageFailureKind.STALE_REVISION, path,
                             "Another session saved a newer checkpoint")
        self.assertEqual(error.kind, StorageFailureKind.STALE_REVISION)
        self.assertEqual(error.path, path)
        self.assertIn(str(path), str(error))


if __name__ == "__main__":
    unittest.main()
