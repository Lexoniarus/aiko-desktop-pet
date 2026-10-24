"""Strict complete preferences shared by SQLite and checked legacy import."""

from typing import Any

from ..application.settings import PetSettings

SETTING_FLAGS = ("always_on_top", "auto_walk", "auto_routine", "follow_cursor",
          "spontaneous_talk", "observe_computer", "learn_rhythm", "online_social")
_COORDINATES = ("x", "y", "toolbar_x", "toolbar_y")


def decode_settings(row: dict[str, Any]) -> PetSettings:
    expected = {*SETTING_FLAGS, *_COORDINATES, "scale", "zodiac_sign"}
    if set(row) != expected:
        raise ValueError("Unsupported saved settings fields")
    for name in SETTING_FLAGS:
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
