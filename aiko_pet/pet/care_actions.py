"""Pure care-action decisions for the PetState aggregate.

Care outcomes include unchanged German fallback text; only PetState applies
the planned need, sleep, meal and friendship mutations.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Protocol

from .food import (
    DEFAULT_FOOD_ID, FOOD_CATALOG, FoodId, FoodState, eat_food,
)
from .friendship import CARE_PRIMARY_NEED
from .need_decay import NeedLevels
from .routine import MEAL_NAMES, context_at
from .value_rules import clamp_need_value


class CareValues(Protocol):
    """Values required to decide a care action without mutating the owner."""

    sleeping: bool
    sleep_origin: str
    auto_sleep_night: str
    nap_until: float
    energy: float
    satiety: float
    mood: float
    social: float
    affection: float
    meals_date: str
    meals_today: list[str]
    food: FoodState


@dataclass(frozen=True, slots=True)
class CareTransition:
    """A validated full snapshot of one care action's intended changes."""

    response: str
    changed: bool
    needs: NeedLevels
    sleeping: bool
    sleep_origin: str
    auto_sleep_night: str
    nap_until: float
    meals_date: str
    meals_today: tuple[str, ...]
    reward_action: str | None = None
    need_before: float = 0.0
    food: FoodState | None = None
    mood_experience: float = 0.0


def plan_care_action(
    state: CareValues, action: str, *, now: float,
    food_id: FoodId | None = None,
) -> CareTransition:
    """Decide old care values, rejection and dialogue without any writes."""
    if action not in {
        "sleep", "feed", "play", "pet", "talk", "energy_drink",
    }:
        raise ValueError(f"Unknown action: {action}")
    if food_id is not None and (action != "feed" or food_id not in FOOD_CATALOG):
        raise ValueError("Food selection only accepts known feed items")
    unchanged = CareTransition(
        response="",
        changed=False,
        needs=NeedLevels(
            state.satiety, state.mood, state.energy,
            state.social, state.affection,
        ),
        sleeping=state.sleeping,
        sleep_origin=state.sleep_origin,
        auto_sleep_night=state.auto_sleep_night,
        nap_until=state.nap_until,
        meals_date=state.meals_date,
        meals_today=tuple(state.meals_today),
    )
    if action == "sleep":
        sleeping = not state.sleeping
        night_key = state.auto_sleep_night
        if not sleeping:
            context = context_at(now)
            if context.night:
                night_key = context.night_key
        return replace(
            unchanged, changed=True,
            response=(
                "Zzz ... gute Nacht." if sleeping else "Oh ... schon Morgen?"
            ),
            sleeping=sleeping,
            sleep_origin="manual" if sleeping else "",
            auto_sleep_night=night_key,
        )
    if action == "play":
        # A bare legacy care action cannot reward a game that was not played.
        message = (
            "Ich bin gerade zu müde zum Spielen." if state.energy < 8
            else "Wähle ein Spiel aus, dann spielen wir!"
        )
        return replace(unchanged, response=message)
    if action == "energy_drink" and state.energy >= 100:
        return replace(
            unchanged, response="Ich bin schon voll. Mehr passt gerade nicht rein.",
        )
    sleeping = False
    sleep_origin = state.sleep_origin
    nap_until = state.nap_until
    night_key = state.auto_sleep_night
    if state.sleeping:
        sleep_origin = ""
        nap_until = 0.0
        context = context_at(now)
        if context.night:
            night_key = context.night_key
    if action == "energy_drink":
        return replace(
            unchanged, changed=True,
            sleeping=sleeping, sleep_origin=sleep_origin,
            nap_until=nap_until, auto_sleep_night=night_key,
            needs=replace(
                unchanged.needs, energy=clamp_need_value(state.energy + 10.0),
            ),
            response="...Oh. Das hat geholfen.",
        )
    need_before = float(getattr(state, CARE_PRIMARY_NEED[action]))
    result = replace(
        unchanged, changed=True,
        sleeping=sleeping, sleep_origin=sleep_origin,
        nap_until=nap_until, auto_sleep_night=night_key,
        reward_action=action, need_before=need_before,
    )
    if action == "talk":
        return replace(
            result,
            needs=replace(
                result.needs,
                social=clamp_need_value(state.social + 26),
                energy=clamp_need_value(state.energy - 1),
            ),
            response="...Du möchtest reden? Ich höre zu.",
        )
    if action == "pet":
        return replace(
            result,
            needs=replace(
                result.needs,
                affection=clamp_need_value(state.affection + 25),
                social=clamp_need_value(state.social + 2),
            ),
            response="... Das ist angenehm.",
        )
    selected_food = food_id if food_id is not None else DEFAULT_FOOD_ID
    profile = FOOD_CATALOG[selected_food]
    intake = eat_food(state.food, state.satiety, selected_food)
    if not intake.accepted:
        return replace(unchanged, response="Ich bin schon satt. ...Wirklich.")
    context = context_at(now)
    meals_date = state.meals_date
    meals = list(state.meals_today)
    if meals_date != context.day_key:
        meals_date = context.day_key
        meals = []
    first_meal = (
        profile.category == "meal"
        and context.meal is not None and context.meal not in meals
    )
    if first_meal and context.meal is not None:
        meals.append(context.meal)
    if intake.repetitive:
        response = f"Schon wieder {profile.display_name}? ...Na gut."
    elif first_meal and context.meal is not None:
        response = f"Danke für das {MEAL_NAMES[context.meal].lower()}!"
    else:
        response = f"Mhm ... {profile.display_name}! Danke."
    return replace(
        result,
        meals_date=meals_date,
        meals_today=tuple(meals),
        food=intake.food,
        mood_experience=intake.mood_change,
        needs=replace(
            result.needs,
            satiety=intake.satiety,
            social=clamp_need_value(state.social + 1),
        ),
        response=response,
    )

def resolve_care_time(now: float | None) -> float:
    """Resolve the clock once per interaction for deterministic transitions."""
    return time.time() if now is None else now
