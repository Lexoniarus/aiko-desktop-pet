"""Food choices are detached presentation values, never mutable pet state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from ...asset_paths import ASSET_ROOT
from ...pet.food import FOOD_CATALOG, FoodId

FoodChoiceId: TypeAlias = FoodId | Literal["energy_drink"]


@dataclass(frozen=True, slots=True)
class FoodChoice:
    id: FoodChoiceId
    name: str
    category_label: str
    satiety_points: float
    image_path: Path
    benefit_label: str = ""


def food_choices() -> tuple[FoodChoice, ...]:
    """Display the single nutrition catalog alongside the separate drink."""
    order: tuple[FoodChoiceId, ...] = (
        "onigiri", "sandwich", "taiyaki", "apple", "dango",
        "energy_drink", "donut", "cookie", "melonpan", "cupcake", "dorayaki",
    )
    images = ASSET_ROOT / "items" / "icons" / "64"
    choices: list[FoodChoice] = []
    for item_id in order:
        if item_id == "energy_drink":
            choices.append(FoodChoice(
                id=item_id, name="Energy Drink", category_label="Getränk",
                satiety_points=0.0,
                image_path=images / "energy_drink.png",
                benefit_label="+10 Energie",
            ))
            continue
        profile = FOOD_CATALOG[item_id]
        choices.append(FoodChoice(
            id=item_id, name=profile.display_name,
            category_label=(
                "Mahlzeit" if profile.category == "meal" else "Snack"
            ),
            satiety_points=profile.instant_satiety_points,
            image_path=images / f"{item_id}.png",
            benefit_label=f"+{profile.instant_satiety_points:.0f} Sättigung",
        ))
    return tuple(choices)
