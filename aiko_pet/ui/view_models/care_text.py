"""Map a committed care effect to the existing authored German fallback."""

from ...pet.care_result import CareEffect, CareResult
from ...pet.content import GERMAN_TEXT
from ...pet.food_catalog import DEFAULT_CATALOG
from .german_object_phrases import object_phrases

_MESSAGES = {
    CareEffect.FOOD_SATISFIED: "care.feed_satisfied",
    CareEffect.PLAY_TIRED: "care.play_tired",
    CareEffect.PLAY_REQUESTED: "care.play_choose",
    CareEffect.DRINK_SATISFIED: "care.energy_full",
    CareEffect.DRINK_CONSUMED: "care.energy_success",
    CareEffect.CONVERSATION: "care.talk",
    CareEffect.AFFECTION: "care.pet",
    CareEffect.AFFECTION_REFUSED: "care.pet_refused",
    CareEffect.SLEEP_STARTED: "care.sleep_start",
    CareEffect.SLEEP_ENDED: "care.sleep_wake",
}


def format_care_response(result: CareResult) -> str:
    """Keep wording and placeholders outside nutrition and care policies."""
    if result.effect == CareEffect.FOOD_MEAL and result.meal_id is None:
        raise ValueError("A consumed main meal needs a meal identifier")
    food_keys = {
        CareEffect.FOOD_MEAL: "care.feed_meal",
        CareEffect.FOOD_REPEAT: "care.feed_repeat",
        CareEffect.FOOD_SNACK: "care.feed_snack",
    }
    if result.effect in food_keys:
        if result.food_id is None:
            raise ValueError("Consumed food needs a food identifier")
        profile = DEFAULT_CATALOG.foods[result.food_id]
        return GERMAN_TEXT.format(
            food_keys[result.effect],
            food=object_phrases(result.food_id, profile.display_name)["item_indef_nom"],
        )
    return GERMAN_TEXT.format(_MESSAGES[result.effect])
