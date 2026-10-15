"""Map a committed care effect to the existing authored German fallback."""

from ...pet.care_result import CareEffect, CareResult
from ...pet.content import GERMAN_TEXT
from ...pet.food_catalog import DEFAULT_CATALOG
from ...pet.routine import MEAL_NAMES

_MESSAGES = {
    CareEffect.FOOD_SATISFIED: "care.feed_satisfied",
    CareEffect.PLAY_TIRED: "care.play_tired",
    CareEffect.PLAY_REQUESTED: "care.play_choose",
    CareEffect.DRINK_SATISFIED: "care.energy_full",
    CareEffect.DRINK_CONSUMED: "care.energy_success",
    CareEffect.CONVERSATION: "care.talk",
    CareEffect.AFFECTION: "care.pet",
    CareEffect.SLEEP_STARTED: "care.sleep_start",
    CareEffect.SLEEP_ENDED: "care.sleep_wake",
}


def format_care_response(result: CareResult) -> str:
    """Keep wording and placeholders outside nutrition and care policies."""
    if result.effect == CareEffect.FOOD_MEAL:
        if result.meal_id is None:
            raise ValueError("A consumed main meal needs a meal identifier")
        return GERMAN_TEXT.format(
            "care.feed_meal", meal=MEAL_NAMES[result.meal_id].lower(),
        )
    if result.effect in (CareEffect.FOOD_REPEAT, CareEffect.FOOD_SNACK):
        if result.food_id is None:
            raise ValueError("Consumed food needs a food identifier")
        key = (
            "care.feed_repeat" if result.effect == CareEffect.FOOD_REPEAT
            else "care.feed_snack"
        )
        return GERMAN_TEXT.format(
            key, food=DEFAULT_CATALOG.foods[result.food_id].display_name,
        )
    return GERMAN_TEXT.format(_MESSAGES[result.effect])
