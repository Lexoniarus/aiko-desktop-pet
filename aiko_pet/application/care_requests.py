"""Choose moderate care requests without changing needs or urgent emotions."""

from __future__ import annotations

from ..pet.balance import BALANCE
from ..pet.care_result import CareResult
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlets import FoodMonotonyParameters, MoodletId
from ..pet.state import PetState


def choose_care_request(state: PetState) -> str | None:
    """Lowest need wins; tuple order provides the explicit tie-break priority."""
    if state.sleeping:
        return None
    event, value = min(
        (
            ("care_request_feed", state.satiety),
            ("care_request_talk", state.social),
            ("care_request_pet", state.affection),
            ("care_request_play", state.fun),
        ),
        key=lambda item: item[1],
    )
    return (
        event if value <= BALANCE.integer("care_requests", "need_threshold") else None
    )


def food_variety_event(state: PetState, result: CareResult) -> str | None:
    """A committed personal meal may voice a request, without claiming delivery."""
    if not result.food_consumed:
        return None
    memory = state.moodlets.interactions.food
    if memory.request_pending:
        return "feed_variety_request"
    parameters = MOODLET_CATALOG.definitions[MoodletId.FOOD_MONOTONY].parameters
    assert isinstance(parameters, FoodMonotonyParameters)
    if (memory.requested_at is not None and memory.ignored_portions
            and state.lived_seconds - memory.requested_at
            < parameters.request_lifetime_seconds):
        return "feed_variety_reminder"
    return None
