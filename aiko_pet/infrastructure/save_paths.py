"""Side-effect-free legacy and planned SQLite save locations.

Environment loading stays in config.py. Resolving a path never reads a save,
creates a directory, imports JSON or selects another destination after failure.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DATABASE_SUFFIXES = frozenset({".sqlite3", ".sqlite", ".db"})


def _user_data_directory() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "AikoDesktopPet"


def _expanded_path(value: str) -> Path:
    candidate = Path(os.path.expandvars(os.path.expanduser(value)))
    return candidate if candidate.is_absolute() else _PROJECT_ROOT / candidate


def default_save_path() -> Path:
    """Keep the active JSON store's existing path behavior and public binding."""
    custom = os.environ.get("AIKO_SAVE_PATH", "").strip()
    return _expanded_path(custom) if custom else _user_data_directory() / "state.json"


@dataclass(frozen=True, slots=True)
class SavePaths:
    database: Path
    legacy_json: Path


def resolve_save_paths(path: Path | None = None) -> SavePaths:
    """Resolve exactly one database and its designated one-time import candidate.

    An explicit path takes precedence over AIKO_SAVE_PATH. Matching outer quotes
    support environment overrides as well as values already unquoted by config.
    Existence, supported JSON content and publication are later import decisions.
    """
    custom = str(path) if path is not None else os.environ.get("AIKO_SAVE_PATH", "")
    custom = custom.strip()
    if len(custom) >= 2 and custom[0] == custom[-1] and custom[0] in ("'", '"'):
        custom = custom[1:-1]
    if not custom:
        directory = _user_data_directory()
        return SavePaths(directory / "state.sqlite3", directory / "state.json")
    candidate = _expanded_path(custom)
    suffix = candidate.suffix.lower()
    if suffix in _DATABASE_SUFFIXES:
        return SavePaths(candidate, candidate.with_suffix(".json"))
    if suffix == ".json":
        return SavePaths(candidate.with_suffix(".sqlite3"), candidate)
    return SavePaths(candidate.with_name(candidate.name + ".sqlite3"), candidate)
