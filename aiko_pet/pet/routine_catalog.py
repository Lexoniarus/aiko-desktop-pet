"""Validated schedule data for Aiko's existing local daily routine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias
from .catalog_validation import load_json, object_fields

DailySlot: TypeAlias = tuple[int, str, str, str | None]
PERIODS = frozenset(
    {
        "night",
        "breakfast",
        "quiet",
        "lunch",
        "free",
        "dinner",
        "evening",
    }
)


@dataclass(frozen=True, slots=True)
class RoutineCatalog:
    weekdays: tuple[DailySlot, ...]
    saturday: tuple[DailySlot, ...]
    sunday: tuple[DailySlot, ...]


def _parse_slots(rows: Any) -> tuple[DailySlot, ...]:
    if not isinstance(rows, list) or not rows:
        raise ValueError("Schedule must contain daily slots")
    slots: list[DailySlot] = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid schedule entry")
        object_fields(
            row, ("minute", "period", "label", "meal"), context="routine slot"
        )
        minute = row.get("minute")
        period, label, meal = (
            row.get("period"),
            row.get("label"),
            row.get("meal"),
        )
        if (
            type(minute) is not int
            or minute < 0
            or minute >= 1440
            or (slots and minute <= slots[-1][0])
            or not isinstance(period, str)
            or period not in PERIODS
            or not isinstance(label, str)
            or not label.strip()
            or meal not in (None, "breakfast", "lunch", "dinner")
            or (meal is not None and meal != period)
        ):
            raise ValueError("Invalid or unordered schedule slot")
        slots.append((minute, period, label, meal))
    if slots[0][0] != 0:
        raise ValueError("Daily schedule must start at midnight")
    return tuple(slots)


def parse_routine_catalog(raw: Any) -> RoutineCatalog:
    object_fields(raw, ("version", "weekdays", "saturday", "sunday"), context="routine")
    if (
        not isinstance(raw, dict)
        or type(raw.get("version")) is not int
        or raw["version"] != 1
    ):
        raise ValueError("Unsupported schedule version")
    return RoutineCatalog(
        weekdays=_parse_slots(raw.get("weekdays")),
        saturday=_parse_slots(raw.get("saturday")),
        sunday=_parse_slots(raw.get("sunday")),
    )


def load_packaged_routine_catalog(
    path: Path = Path(__file__).resolve().parents[1] / "data" / "routine.de.json",
) -> RoutineCatalog:
    return parse_routine_catalog(load_json(path))


ROUTINE_CATALOG = load_packaged_routine_catalog()
