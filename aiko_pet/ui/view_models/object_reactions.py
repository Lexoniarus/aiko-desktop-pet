"""Format known object names from the canonical item catalog, without decisions."""

from dataclasses import replace

from ...pet.animation.item_assets import ItemCatalog
from ...pet.content import GERMAN_TEXT
from ...pet.mind.catalog import Reaction


def format_object_reaction(
    reaction: Reaction,
    identity: str | None,
    items: ItemCatalog,
) -> Reaction:
    if not reaction.event.startswith("object_"):
        return reaction
    item = items.foods.get(identity) if identity is not None else None
    values = {
        "item": item.label
        if item is not None
        else GERMAN_TEXT.format("world.unknown_item")
    }
    return replace(
        reaction,
        beats=tuple(
            type(beat).text(beat.content.format_map(values))
            if beat.kind == "text"
            else beat
            for beat in reaction.beats
        ),
    )
