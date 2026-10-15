"""Validated packaged food records, independent of nutrition calculations.

The model and parser accept already-decoded records. One packaged JSON read
provides the shipped defaults; alternative storage backends can reuse the
schema without embedding nutrition entries in Python source.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, TypeAlias, cast

FoodId: TypeAlias = str
FoodCategory = Literal["meal", "snack"]


@dataclass(frozen=True, slots=True)
class FoodProfile:
    """Stable nutrition data for one named food item."""

    id: FoodId
    display_name: str
    category: FoodCategory
    instant_satiety_points: float
    digest_reserve_minutes: float
    normal_mood_bonus: float


@dataclass(frozen=True, slots=True)
class FoodCatalog:
    """Validated menu order and immutable nutrition records."""

    foods: Mapping[FoodId, FoodProfile]
    default_food_id: FoodId
    menu_order: tuple[str, ...]


def parse_food_catalog(data: Any) -> FoodCatalog:
    """Reject malformed, inconsistent and nonfinite packaged food records."""
    if not isinstance(data, dict) or type(data.get("version")) is not int:
        raise ValueError("Food catalogue must have an integer version")
    if data["version"] != 1:
        raise ValueError("Unsupported food catalogue version")
    rows = data.get("foods")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Food catalogue must have food records")
    profiles: dict[FoodId, FoodProfile] = {}
    fields = (
        "instant_satiety_points", "digest_reserve_minutes",
        "normal_mood_bonus",
    )
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid food record")
        key = row.get("id")
        title = row.get("display_name")
        category = row.get("category")
        if (
            not isinstance(key, str) or not key.isidentifier()
            or not isinstance(title, str) or not title.strip()
            or category not in ("meal", "snack") or key in profiles
        ):
            raise ValueError("Invalid or duplicate food ID, title or category")
        values = tuple(row.get(field) for field in fields)
        if any(
            type(value) not in (int, float)
            or not math.isfinite(value) or not 0 <= value <= maximum
            for value, maximum in zip(values, (100, 175, 20))
        ):
            raise ValueError(f"Invalid nutrition parameters for {key}")
        profiles[key] = FoodProfile(
            key, title, cast(FoodCategory, category),
            float(values[0]), float(values[1]), float(values[2]),
        )
    default = data.get("default_food_id")
    if not isinstance(default, str) or default not in profiles:
        raise ValueError("Default food must belong to the food catalogue")
    order = data.get("menu_order")
    if (
        not isinstance(order, list)
        or any(not isinstance(key, str) for key in order)
        or len(set(order)) != len(order)
        or set(order) != set(profiles) | {"energy_drink"}
    ):
        raise ValueError("Menu order must list each food and the energy drink")
    return FoodCatalog(MappingProxyType(profiles), default, tuple(order))


def load_packaged_food_catalog(
    path: Path = Path(__file__).resolve().parents[1] / "data" / "food_catalog.json",
) -> FoodCatalog:
    """Read validated read-only default resources once for the local pet."""
    return parse_food_catalog(json.loads(path.read_text(encoding="utf-8")))


DEFAULT_CATALOG = load_packaged_food_catalog()
