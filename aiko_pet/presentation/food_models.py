"""Food choices are detached presentation values, never mutable pet state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..asset_paths import ASSET_ROOT
from ..pet.food import FOOD_CATALOG, FoodId


@dataclass(frozen=True, slots=True)
class FoodChoice:
    id: FoodId
    name: str
    category_label: str
    satiety_points: float
    image_path: Path


def food_choices() -> tuple[FoodChoice, ...]:
    """Map the five editable food definitions into a stable menu order."""
    order: tuple[FoodId, ...] = (
        "onigiri", "sandwich", "taiyaki", "apple", "dango",
    )
    return tuple(
        FoodChoice(
            id=food_id,
            name=FOOD_CATALOG[food_id].display_name,
            category_label=(
                "Mahlzeit" if FOOD_CATALOG[food_id].category == "meal"
                else "Snack"
            ),
            satiety_points=FOOD_CATALOG[food_id].instant_satiety_points,
            image_path=ASSET_ROOT / "food" / f"{food_id}.png",
        )
        for food_id in order
    )
