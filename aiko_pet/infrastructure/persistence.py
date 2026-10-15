"""Versioned, atomic local JSON persistence for the desktop pet."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from ..application import settings as app_settings
from ..application.session import LoadedPetData
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.mind.adaptive_models import AdaptiveMemory
from ..pet.state import PetState
from ..world.contracts import WorldSnapshot
from .item_assets import load_item_catalog
from .pet_codec import decode_pet_state, encode_pet_state
from .world_catalog import build_consumable_definitions
from .world_codec import decode_world, encode_world

SCHEMA_VERSION = 1


def default_save_path() -> Path:
    custom_path = os.environ.get("AIKO_SAVE_PATH", "").strip()
    if custom_path:
        candidate = Path(os.path.expandvars(os.path.expanduser(custom_path)))
        if not candidate.is_absolute():
            candidate = Path(__file__).resolve().parents[2] / candidate
        return candidate
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    return base / "AikoDesktopPet" / "state.json"


class StateStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_save_path()
        self._invalid_world = False

    def _read_payload(self) -> dict[str, Any] | None:
        """Return only supported versioned JSON, without advancing the pet."""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, ValueError, OSError, UnicodeError):
            return None
        if (
            not isinstance(payload, dict)
            or type(payload.get("version")) is not int
            or payload.get("version") != SCHEMA_VERSION
        ):
            return None
        return payload

    def load_session(self, *, now: float | None = None) -> LoadedPetData:
        """Read the complete session in one I/O operation, without simulation."""
        current = time.time() if now is None else now
        payload = self._read_payload()
        if payload is None:
            return LoadedPetData(
                state=PetState(updated_at=current),
                settings=app_settings.PetSettings(),
                adaptive_memory=AdaptiveMemory(),
                restored_from_save=False,
            )
        saved_world: WorldSnapshot | None = None
        if "world" in payload:
            try:
                saved_world = decode_world(
                    payload["world"], build_consumable_definitions(
                        DEFAULT_CATALOG, load_item_catalog(),
                    ),
                )
            except (ValueError, TypeError, OverflowError):
                self._invalid_world = True
        return LoadedPetData(
            state=decode_pet_state(payload.get("pet"), now=current),
            settings=app_settings.PetSettings.from_dict(payload.get("settings")),
            adaptive_memory=AdaptiveMemory.from_dict(payload.get("adaptive")),
            restored_from_save=True,
            world=saved_world,
        )

    def save(self, pet: PetState, settings: app_settings.PetSettings,
             *, adaptive: AdaptiveMemory | None = None,
             world: WorldSnapshot | None = None, world_recovery_x: float = 0) -> None:
        """Don't leave a half-written save on power loss or interruption."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._preserve_unreadable_save()
        payload = {
            "version": SCHEMA_VERSION,
            "pet": encode_pet_state(pet),
            "settings": settings.to_dict(),
        }
        if adaptive is not None:
            payload["adaptive"] = adaptive.to_dict()
        if world is not None:
            payload["world"] = encode_world(world, recovery_x=world_recovery_x)
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

    def _preserve_unreadable_save(self) -> None:
        """Keep corrupt/future-version data before a fresh session replaces it."""
        try:
            contents = self.path.read_bytes()
        except FileNotFoundError:
            return
        try:
            payload = json.loads(contents.decode("utf-8"))
        except (ValueError, UnicodeError):
            payload = None
        if (
            isinstance(payload, dict)
            and type(payload.get("version")) is int
            and payload["version"] == SCHEMA_VERSION
            and not self._invalid_world
        ):
            return
        backup = self.path.with_name(
            f"{self.path.stem}-{uuid.uuid4().hex}.aiko-save-backup"
        )
        # Exclusive creation never overwrites another backup. If it fails,
        # propagate the I/O error and leave the original save untouched.
        with backup.open("xb") as file:
            file.write(contents)
            file.flush()
            os.fsync(file.fileno())
        self._invalid_world = False
