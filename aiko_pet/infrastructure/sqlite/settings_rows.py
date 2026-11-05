"""Application preferences in columns; no forgiving reset of present values."""

from __future__ import annotations

import sqlite3

from ...application.settings import PetSettings
from ..settings_codec import SETTING_FLAGS, decode_settings
from .rows import boolean, singleton, upsert_singleton


def write_settings(connection: sqlite3.Connection, settings: PetSettings) -> None:
    row = settings.to_dict()
    row.setdefault("zodiac_sign", None)
    decode_settings(row)
    row.update((name, 1 if row[name] else 0) for name in SETTING_FLAGS)
    upsert_singleton(connection, "app_settings", row)


def read_settings(connection: sqlite3.Connection) -> PetSettings:
    row = singleton(connection, "app_settings")
    del row["id"]
    row.update((name, boolean(row[name])) for name in SETTING_FLAGS)
    return decode_settings(row)
