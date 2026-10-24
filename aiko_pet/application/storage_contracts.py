"""Backend-independent failures and revision values for coherent saved sessions.

These values do not write state or advance time. The runtime SQLite adapter
uses them for complete snapshot writes and last-successful revision ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

MAX_SAVE_REVISION = 2**63 - 1


class StorageFailureKind(StrEnum):
    ACCESS = "access"
    IO = "io"
    LOCKED = "locked"
    STALE_REVISION = "stale_revision"
    INVALID_DATA = "invalid_data"
    INVALID_DATABASE = "invalid_database"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    DATABASE = "database"


class StorageError(Exception):
    """A storage failure with its affected path, without a backend exception API."""

    def __init__(
        self, kind: StorageFailureKind, path: Path, message: str,
    ) -> None:
        self.kind = kind
        self.path = path
        self.message = message
        super().__init__(f"{message} [{kind.value}: {path}]")


@dataclass(frozen=True, slots=True)
class SaveRevision:
    """Expected persisted revision; zero means no committed checkpoint yet.

    A writer returns a newer value only after its transaction commits. Holding
    this value grants no permission to merge or overwrite a different revision.
    """

    value: int = 0

    def __post_init__(self) -> None:
        if type(self.value) is not int or not 0 <= self.value <= MAX_SAVE_REVISION:
            raise ValueError("Save revision must be a nonnegative 64-bit integer")
