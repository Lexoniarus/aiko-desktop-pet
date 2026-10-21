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
from ..application.social_history import SocialContentHistory
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.mind.adaptive_models import AdaptiveMemory
from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..pet.mind.quiet_rhythm import QuietWindow
from ..pet.state import PetState
from ..world.contracts import ObjectInteraction, WorldSnapshot
from .friendship_codec import valid_friendship
from .item_assets import load_item_catalog
from .moodlet_codec import valid_moodlets
from .object_memory_codec import decode_object_memory, encode_object_memory
from .pet_codec import decode_pet_state, encode_pet_state, valid_pet_time
from .sleep_codec import valid_sleep
from .social_history_codec import (
    decode_social_history,
    encode_social_history,
    valid_social_history,
)
from .wish_codec import valid_wishes
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
        self._invalid_memory = False

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
        saved_memory: ObjectMemorySnapshot | None = None
        if "object_memory" in payload:
            if saved_world is None:
                # Instance IDs have meaning only within their paired World.
                self._invalid_memory = True
            else:
                try:
                    memory = decode_object_memory(payload["object_memory"], {
                        item.food_id or item.definition_id:
                        "drink" if ObjectInteraction.DRINK in item.interactions
                        else "food" for item in saved_world.definitions
                    }, allocated_until=saved_world.next_instance_id)
                    saved_memory = memory
                except (ValueError, TypeError, OverflowError):
                    self._invalid_memory = True
        social_history = SocialContentHistory()
        if "social_history" in payload:
            try:
                social_history = decode_social_history(payload["social_history"])
            except (ValueError, TypeError, OverflowError):
                # Pet/world recovery stays independent; preserve malformed input
                # through the existing backup path before any replacement save.
                pass
        return LoadedPetData(
            social_history=social_history,
            state=decode_pet_state(payload.get("pet"), now=current),
            settings=app_settings.PetSettings.from_dict(payload.get("settings")),
            adaptive_memory=AdaptiveMemory.from_dict(payload.get("adaptive")),
            restored_from_save=True,
            world=saved_world,
            object_memory=saved_memory,
        )

    def save(self, pet: PetState, settings: app_settings.PetSettings,
             *, adaptive: AdaptiveMemory | None = None,
             world: WorldSnapshot | None = None, world_recovery_x: float = 0,
             object_memory: ObjectMemorySnapshot | None = None,
             social_history: SocialContentHistory | None = None) -> None:
        """Don't leave a half-written save on power loss or interruption."""
        if object_memory is not None and world is None:
            raise ValueError("Object memory requires its paired World snapshot")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._preserve_unreadable_save()
        payload = {
            "version": SCHEMA_VERSION,
            "pet": encode_pet_state(pet),
            "settings": settings.to_dict(),
        }
        if social_history is not None:
            payload["social_history"] = encode_social_history(social_history)
        if adaptive is not None:
            payload["adaptive"] = adaptive.to_dict()
        if world is not None:
            payload["world"] = encode_world(world, recovery_x=world_recovery_x)
        if object_memory is not None:
            assert world is not None
            payload["object_memory"] = encode_object_memory(
                object_memory, world_next_id=world.next_instance_id,
            )
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
        pet_data = payload.get("pet") if isinstance(payload, dict) else None
        invalid_time = (
            isinstance(pet_data, dict) and "time" in pet_data
            and not valid_pet_time(pet_data["time"])
        )
        invalid_sections = False
        if isinstance(pet_data, dict):
            saved_time = pet_data.get("time")
            elapsed = (saved_time.get("lived_seconds", 0)
                       if isinstance(saved_time, dict) else 0)
            invalid_sections = any(
                invalid_time or not validate(pet_data[key], elapsed)
                for key, validate in (
                    ("relationship", valid_friendship), ("sleep_episode", valid_sleep),
                    ("moodlets", valid_moodlets), ("wishes", valid_wishes),
                ) if key in pet_data
            )
        invalid_social = (isinstance(payload, dict) and "social_history" in payload
                          and not valid_social_history(payload["social_history"]))
        invalid_quiet = False
        adaptive = payload.get("adaptive") if isinstance(payload, dict) else None
        if isinstance(adaptive, dict) and "quiet_window" in adaptive:
            try:
                QuietWindow.from_dict(adaptive["quiet_window"])
            except (ValueError, TypeError, KeyError, OverflowError):
                invalid_quiet = True
        if (
            isinstance(payload, dict)
            and type(payload.get("version")) is int
            and payload["version"] == SCHEMA_VERSION
            and not self._invalid_world
            and not self._invalid_memory
            and not invalid_time
            and not invalid_sections and not invalid_quiet and not invalid_social
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
        self._invalid_memory = False
