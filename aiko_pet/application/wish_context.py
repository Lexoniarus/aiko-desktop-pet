"""One capability projection shared by desktop attention and room forecasts."""

from ..pet.balance import BALANCE
from ..pet.interaction_rules import petting_is_welcome
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlets import MoodletId
from ..pet.state import PetState
from ..pet.wishes import WishContext


def wish_context_for(
    state: PetState,
    *,
    online_social: bool,
    prepared_social: frozenset[str] = frozenset(),
) -> WishContext:
    active = {episode.definition_id for episode in state.moodlets.active}
    return WishContext(
        online_social=online_social,
        prepared_social=prepared_social,
        petting_welcome=petting_is_welcome(
            state.moodlets,
            affection=state.affection,
            friendship_level=state.friendship_level,
            elapsed=state.lived_seconds,
            definitions=MOODLET_CATALOG.definitions,
        ),
        games_ready=state.energy >= BALANCE.integer("care", "play_minimum_energy"),
        crowded=MoodletId.CROWDED in active,
        petting_refused=state.lived_seconds
        < state.moodlets.interactions.petting_refused_until,
        repetitive_food=state.moodlets.interactions.food.food_id
        if MoodletId.FOOD_MONOTONY in active
        else None,
    )
