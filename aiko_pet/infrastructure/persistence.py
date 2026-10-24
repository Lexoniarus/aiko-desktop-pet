"""Configured SQLite session store with one-time strict legacy JSON import."""

from __future__ import annotations

from pathlib import Path

from ..application.session import LoadedPetData
from .save_paths import default_save_path as default_save_path
from .save_paths import resolve_save_paths
from .sqlite.legacy_import import load_or_import_session
from .sqlite.store import SqliteStateStore


class StateStore(SqliteStateStore):
    """Resolve one save and reuse the complete SQLite writer without revision cache."""

    def __init__(self, path: Path | None = None) -> None:
        self.paths = resolve_save_paths(path)
        super().__init__(self.paths.database)

    def load_session(self, *, now: float | None = None) -> LoadedPetData:
        return load_or_import_session(self.paths, now=now)
