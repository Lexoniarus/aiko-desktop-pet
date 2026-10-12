"""Optional local configuration without third-party dependencies."""

from __future__ import annotations

import os
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SUPPORTED_KEYS = frozenset({"AIKO_SAVE_PATH"})


def load_env_file(path: Path | None = None) -> None:
    """Read supported, non-empty KEY=VALUE lines from the local .env file.

    Already-set environment values take precedence. The file is optional and
    arbitrary environment keys are intentionally not imported.
    """
    source = _PROJECT_ROOT / ".env" if path is None else path
    try:
        contents = source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if key not in _SUPPORTED_KEYS:
            continue
        value = raw_value.strip()
        if (len(value) >= 2 and value[0] == value[-1]
                and value[0] in ('"', "'")):
            value = value[1:-1]
        if value and key not in os.environ:
            os.environ[key] = value
