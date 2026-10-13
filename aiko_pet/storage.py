"""Versioned, atomic local JSON persistence for the desktop pet."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .adaptive_models import AdaptiveMemory
from .application.session import LoadedPetData
from .application.settings import PetSettings as PetSettings
from .domain import PetState

SCHEMA_VERSION = 1


def default_save_path() -> Path:
    custom_path = os.environ.get("AIKO_SAVE_PATH", "").strip()
    if custom_path:
        candidate = Path(os.path.expandvars(os.path.expanduser(custom_path)))
        if not candidate.is_absolute():
            candidate = Path(__file__).resolve().parents[1] / candidate
        return candidate
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "AikoDesktopPet" / "state.json"


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_save_path()

    def _read_payload(self) -> dict[str, Any] | None:
        """Return only supported versioned JSON, without advancing the pet."""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError, OSError, UnicodeError):
            return None
        if not isinstance(payload, dict) or payload.get("version") != SCHEMA_VERSION:
            return None
        return payload

    def load_session(self, *, now: float | None = None) -> LoadedPetData:
        """Read the complete session in one I/O operation, without simulation."""
        current = time.time() if now is None else now
        payload = self._read_payload()
        if payload is None:
            return LoadedPetData(
                state=PetState(updated_at=current),
                settings=PetSettings(),
                adaptive_memory=AdaptiveMemory(),
                restored_from_save=False,
            )
        return LoadedPetData(
            state=PetState.from_dict(payload.get("pet"), now=current),
            settings=PetSettings.from_dict(payload.get("settings")),
            adaptive_memory=AdaptiveMemory.from_dict(payload.get("adaptive")),
            restored_from_save=True,
        )

    def load(self, *, now: float | None = None) -> tuple[PetState, PetSettings]:
        """Legacy load API: decode saved fields but never advance game time."""
        loaded = self.load_session(now=now)
        return loaded.state, loaded.settings

    def load_memory(self) -> AdaptiveMemory:
        """Legacy adaptive-memory reader, preserving pre-profile saves."""
        payload = self._read_payload()
        if payload is None:
            return AdaptiveMemory()
        return AdaptiveMemory.from_dict(payload.get("adaptive"))

    def save(self, pet: PetState, settings: PetSettings,
             *, adaptive: AdaptiveMemory | None = None) -> None:
        """Don't leave a half-written save on power loss or interruption."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": SCHEMA_VERSION,
            "pet": pet.to_dict(),
            "settings": settings.to_dict(),
        }
        if adaptive is not None:
            payload["adaptive"] = adaptive.to_dict()
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", newline="\n", prefix=".aiko-",
                suffix=".tmp", dir=self.path.parent, delete=False
            ) as file:
                temporary = file.name
                json.dump(payload, file, indent=2, ensure_ascii=False, allow_nan=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                try:
                    Path(temporary).unlink(missing_ok=True)
                except OSError:
                    pass
