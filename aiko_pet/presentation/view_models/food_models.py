"""Food choices are detached presentation values, never mutable pet state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias

from ...pet.animation.item_assets import ItemCatalog
from ...pet.balance import BALANCE
from ...pet.content import GERMAN_TEXT
from ...pet.food import FOOD_CATALOG, FOOD_MENU_ORDER, FoodId

FoodChoiceId: TypeAlias = FoodId | Literal["energy_drink"]


@dataclass(frozen=True, slots=True)
class FoodChoice:
    id: FoodChoiceId
    name: str
    category_label: str
    satiety_points: float
    image_path: Path
    benefit_label: str = ""


def food_choices(items: ItemCatalog) -> tuple[FoodChoice, ...]:
    """Build immutable menu entries from one nutrition and asset catalogue."""
    if set(items.foods) != set(FOOD_MENU_ORDER):
        raise ValueError("The prepared item catalogue must cover the food menu")
    choices: list[FoodChoice] = []
    for item_id in FOOD_MENU_ORDER:
        item = items.foods[item_id]
        if item.icon is None:
            raise ValueError(f"Food {item_id} has no menu icon")
        icon = item.icon
        if item_id == "energy_drink":
            choices.append(
                FoodChoice(
                    id=item_id,
                    name=item.label,
                    category_label=GERMAN_TEXT.format("ui.energy_drink_category"),
                    satiety_points=0.0,
                    image_path=icon,
                    benefit_label=GERMAN_TEXT.format(
                        "ui.energy_drink_benefit",
                        points=f"{BALANCE.number('care', 'energy_drink_gain'):.0f}",
                    ),
                )
            )
            continue
        profile = FOOD_CATALOG[item_id]
        choices.append(
            FoodChoice(
                id=item_id,
                name=item.label,
                category_label=(
                    GERMAN_TEXT.format("ui.food_category_meal")
                    if profile.category == "meal"
                    else GERMAN_TEXT.format("ui.food_category_snack")
                ),
                satiety_points=profile.instant_satiety_points,
                image_path=icon,
                benefit_label=GERMAN_TEXT.format(
                    "ui.food_benefit",
                    points=f"{profile.instant_satiety_points:.0f}",
                ),
            )
        )
    return tuple(choices)
