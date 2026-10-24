"""Application preferences in columns; no forgiving reset of present values."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...application.settings import PetSettings
from .rows import boolean, singleton, upsert_singleton

_FLAGS = ("always_on_top", "auto_walk", "auto_routine", "follow_cursor",
          "spontaneous_talk", "observe_computer", "learn_rhythm", "online_social")
_COORDINATES = ("x", "y", "toolbar_x", "toolbar_y")


def _checked_settings(row: dict[str, Any]) -> PetSettings:
    expected = {*_FLAGS, *_COORDINATES, "scale", "zodiac_sign"}
    if set(row) != expected:
        raise ValueError("Unsupported saved settings fields")
    for name in _FLAGS:
        if type(row[name]) is not bool:
            raise ValueError("Invalid saved behavior flag")
    for name in _COORDINATES:
        value = row[name]
        if value is not None and (
            type(value) is not int or not -20000 <= value <= 20000
        ):
            raise ValueError("Invalid saved window coordinate")
    if type(row["scale"]) is not int or row["scale"] not in (1, 2):
        raise ValueError("Invalid saved scale")
    settings = PetSettings.from_dict(row)
    restored = settings.to_dict()
    restored.setdefault("zodiac_sign", None)
    if restored != row:
        raise ValueError("Saved preferences would be normalized or lost")
    return settings


def write_settings(connection: sqlite3.Connection, settings: PetSettings) -> None:
    row = settings.to_dict()
    row.setdefault("zodiac_sign", None)
    _checked_settings(row)
    row.update((name, 1 if row[name] else 0) for name in _FLAGS)
    upsert_singleton(connection, "app_settings", row)


def read_settings(connection: sqlite3.Connection) -> PetSettings:
    row = singleton(connection, "app_settings")
    del row["id"]
    row.update((name, boolean(row[name])) for name in _FLAGS)
    return _checked_settings(row)
