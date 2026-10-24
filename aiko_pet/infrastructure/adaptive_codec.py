"""Strict, lossless adaptive values for SQL mapping and later checked import.

The legacy model decoder remains forgiving. Check primitive types first, then
reject anything it would normalize instead of duplicating its numeric limits.
"""

from dataclasses import asdict
from typing import Any

from ..pet.catalog_validation import number_value, object_fields
from ..pet.mind.adaptive_models import SLOTS, AdaptiveMemory
from ..pet.mind.quiet_rhythm import QuietWindow

PROFILE_FIELDS = ("hour_seconds", "busy_seconds", "present_seconds", "observed_days")
SCALAR_FIELDS = (
    "strain",
    "settled_work",
    "session_seconds",
    "rest_seconds",
    "last_session_seconds",
    "last_work_wall",
    "last_contact_wall",
    "last_seen_wall",
)


def encode_adaptive(memory: AdaptiveMemory) -> dict[str, Any]:
    row = asdict(memory)
    row["quiet_window"] = memory.quiet_window.to_dict()
    return row


def decode_adaptive(raw: Any) -> AdaptiveMemory:
    row = object_fields(
        raw,
        (
            *PROFILE_FIELDS,
            *SCALAR_FIELDS,
            "last_slot_key",
            "profile_day",
            "quiet_window",
        ),
        context="adaptive memory",
    )
    for name in PROFILE_FIELDS:
        values = row[name]
        if not isinstance(values, list) or len(values) != SLOTS:
            raise ValueError("Adaptive memory requires all hour-of-week slots")
        for value in values:
            number_value(value, minimum=0, maximum=float("inf"), context=name)
    for name in SCALAR_FIELDS:
        number_value(row[name], minimum=0, maximum=float("inf"), context=name)
    if any(not isinstance(row[name], str) for name in ("last_slot_key", "profile_day")):
        raise ValueError("Adaptive calendar anchors require text")
    QuietWindow.from_dict(row["quiet_window"])
    restored = AdaptiveMemory.from_dict(row)
    if encode_adaptive(restored) != row:
        raise ValueError("Adaptive memory would be normalized or reset")
    return restored
