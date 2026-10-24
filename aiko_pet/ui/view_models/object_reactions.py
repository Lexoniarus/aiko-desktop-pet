"""Format known object names from the canonical item catalog, without decisions."""

from dataclasses import replace

from ...pet.animation.item_assets import ItemCatalog
from ...pet.mind.catalog import Reaction
from .german_object_phrases import object_phrases


def format_object_reaction(
    reaction: Reaction,
    identity: str | None,
    items: ItemCatalog,
) -> Reaction:
    if not reaction.event.startswith("object_"):
        return reaction
    item = items.foods.get(identity) if identity is not None else None
    values = object_phrases(identity, item.label if item is not None else None)
    return replace(
        reaction,
        beats=tuple(
            type(beat).text(beat.content.format_map(values))
            if beat.kind == "text"
            else beat
            for beat in reaction.beats
        ),
    )
