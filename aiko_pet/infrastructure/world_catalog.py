"""Compose World definitions from validated food and visual catalogs."""

from __future__ import annotations

from ..pet.animation.item_assets import ItemCatalog
from ..pet.food_catalog import FoodCatalog
from ..world.contracts import ObjectDefinition, ObjectInteraction


def build_food_object_definitions(
    foods: FoodCatalog, items: ItemCatalog,
) -> tuple[ObjectDefinition, ...]:
    """Reference existing IDs only; energy drinks need their own future rules."""
    definitions: list[ObjectDefinition] = []
    for food_id, profile in foods.foods.items():
        visual = items.foods.get(food_id)
        if profile.id != food_id or visual is None or visual.key != food_id:
            raise ValueError(f"Food and visual identities disagree: {food_id}")
        definitions.append(ObjectDefinition(
            definition_id=food_id, asset_id=visual.key, food_id=profile.id,
            interactions=frozenset((ObjectInteraction.EAT,)),
        ))
    return tuple(definitions)
