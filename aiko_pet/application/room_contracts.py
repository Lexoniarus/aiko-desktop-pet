"""Finite browser/native room transport. No Python evaluation command exists."""

from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

PROTOCOL_VERSION = 1
ROOM_COMMANDS = frozenset({
    "snapshot", "tick", "suspend", "resume", "care", "call", "place", "move",
    "offer", "speech_next", "speech_ack", "game_open", "game_action", "game_close",
    "wish_pin", "wish_dismiss", "settings", "social", "horoscope", "forecast",
})


def json_value(value: Any) -> Any:
    """Only detached public values cross the bridge; no live owners or paths."""
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        return json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [json_value(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("Unsupported room transport value")
