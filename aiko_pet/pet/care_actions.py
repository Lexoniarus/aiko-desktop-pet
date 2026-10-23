"""Pure care-action decisions for the PetState aggregate.

Care outcomes describe semantic effects; only PetState applies the planned
need, sleep, meal and friendship mutations. Display text belongs to the UI.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Protocol, cast

from .balance import BALANCE
from .care_result import CARE_ACTIONS, CareAction, CareEffect, CareResult
from .food import (
    DEFAULT_FOOD_ID,
    FOOD_CATALOG,
    FoodId,
    FoodState,
    eat_food,
)
from .interaction_events import PettingAttempted
from .interaction_rules import InteractionConsequences, apply_interaction_event
from .moodlet_catalog import MOODLET_CATALOG
from .moodlets import MoodletState
from .needs import NeedLevels
from .routine import context_at
from .value_rules import clamp_need_value
from .wish_catalog import WISH_CATALOG
from .wish_matching import assign_activity_wish
from .wishes import WishArea, WishState


class CareValues(Protocol):
    """Read-only care inputs; history is exposed as a sequence."""

    @property
    def sleeping(self) -> bool: ...

    @property
    def sleep_origin(self) -> str: ...

    @property
    def auto_sleep_night(self) -> str: ...

    @property
    def nap_until(self) -> float: ...

    @property
    def energy(self) -> float: ...

    @property
    def satiety(self) -> float: ...

    @property
    def fun(self) -> float: ...

    @property
    def social(self) -> float: ...

    @property
    def affection(self) -> float: ...

    @property
    def meals_date(self) -> str: ...

    @property
    def meals_today(self) -> Sequence[str]: ...

    @property
    def food(self) -> FoodState: ...

    @property
    def moodlets(self) -> MoodletState: ...

    @property
    def friendship_level(self) -> int: ...

    @property
    def lived_seconds(self) -> float: ...

    @property
    def wishes(self) -> WishState: ...


@dataclass(frozen=True, slots=True)
class CareTransition:
    """A validated value describing one care action's intended changes."""

    result: CareResult
    changed: bool
    needs: NeedLevels
    sleeping: bool
    sleep_origin: str
    auto_sleep_night: str
    nap_until: float
    meals_date: str
    meals_today: tuple[str, ...]
    contact_action: str | None = None
    food: FoodState | None = None
    interaction: InteractionConsequences | None = None
    wish_instance_id: int | None = None


def plan_care_action(
    state: CareValues,
    action: str,
    *,
    now: float,
    food_id: FoodId | None = None,
) -> CareTransition:
    """Decide care effects and rejection once, without writes or display text."""
    if action not in CARE_ACTIONS:
        raise ValueError(f"Unknown action: {action}")
    if food_id is not None and (action != "feed" or food_id not in FOOD_CATALOG):
        raise ValueError("Food selection only accepts known feed items")
    unchanged = CareTransition(
        result=CareResult(cast(CareAction, action), CareEffect.PLAY_REQUESTED),
        changed=False,
        needs=NeedLevels(
            state.satiety,
            state.energy,
            state.fun,
            state.social,
            state.affection,
        ),
        sleeping=state.sleeping,
        sleep_origin=state.sleep_origin,
        auto_sleep_night=state.auto_sleep_night,
        nap_until=state.nap_until,
        meals_date=state.meals_date,
        meals_today=tuple(state.meals_today),
    )
    if action == "pet":
        wish = assign_activity_wish(
            state.wishes, WishArea.AFFECTION, "pet", elapsed=state.lived_seconds,
            definitions=WISH_CATALOG.definitions,
        )
        interaction = apply_interaction_event(
            state.moodlets, PettingAttempted(
                state.affection, state.friendship_level, wished_for=wish is not None,
            ),
            elapsed=state.lived_seconds, definitions=MOODLET_CATALOG.definitions,
        )
        unchanged = replace(unchanged, interaction=interaction,
                            wish_instance_id=wish.instance_id if wish else None)
        if interaction.refused:
            assert interaction.petting_effect is not None
            return replace(unchanged,
                           result=CareResult("pet", interaction.petting_effect))
    if action == "sleep":
        sleeping = not state.sleeping
        night_key = state.auto_sleep_night
        if not sleeping:
            context = context_at(now)
            if context.night:
                night_key = context.night_key
        return replace(
            unchanged,
            changed=True,
            result=CareResult(
                "sleep",
                CareEffect.SLEEP_STARTED if sleeping else CareEffect.SLEEP_ENDED,
            ),
            sleeping=sleeping,
            sleep_origin="manual" if sleeping else "",
            auto_sleep_night=night_key,
        )
    if action == "play":
        # A bare legacy care action cannot reward a game that was not played.
        effect = (
            CareEffect.PLAY_TIRED
            if state.energy < BALANCE.integer("care", "play_minimum_energy")
            else CareEffect.PLAY_REQUESTED
        )
        return replace(unchanged, result=CareResult("play", effect))
    if action == "energy_drink" and state.energy >= 100:
        return replace(
            unchanged,
            result=CareResult("energy_drink", CareEffect.DRINK_SATISFIED),
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
            unchanged,
            changed=True,
            sleeping=sleeping,
            sleep_origin=sleep_origin,
            nap_until=nap_until,
            auto_sleep_night=night_key,
            needs=replace(
                unchanged.needs,
                energy=clamp_need_value(
                    state.energy + BALANCE.number("care", "energy_drink_gain")
                ),
            ),
            result=CareResult("energy_drink", CareEffect.DRINK_CONSUMED),
            contact_action="energy_drink",
        )
    result = replace(
        unchanged,
        changed=True,
        sleeping=sleeping,
        sleep_origin=sleep_origin,
        nap_until=nap_until,
        auto_sleep_night=night_key,
        contact_action=action,
    )
    if action == "talk":
        return replace(
            result,
            needs=replace(
                result.needs,
                social=clamp_need_value(
                    state.social + BALANCE.integer("care", "talk_social_gain")
                ),
                energy=clamp_need_value(
                    state.energy - BALANCE.integer("care", "talk_energy_cost")
                ),
            ),
            result=CareResult("talk", CareEffect.CONVERSATION),
        )
    if action == "pet":
        assert result.interaction is not None
        assert result.interaction.petting_effect is not None
        return replace(
            result,
            needs=replace(
                result.needs,
                affection=clamp_need_value(
                    state.affection + BALANCE.integer("care", "pet_affection_gain")
                ),
                social=clamp_need_value(
                    state.social + BALANCE.integer("care", "pet_social_gain")
                ),
            ),
            result=CareResult("pet", result.interaction.petting_effect),
        )
    selected_food = food_id if food_id is not None else DEFAULT_FOOD_ID
    profile = FOOD_CATALOG[selected_food]
    intake = eat_food(state.food, state.satiety, selected_food)
    if not intake.accepted:
        return replace(
            unchanged,
            result=CareResult("feed", CareEffect.FOOD_SATISFIED),
        )
    context = context_at(now)
    meals_date = state.meals_date
    meals = list(state.meals_today)
    if meals_date != context.day_key:
        meals_date = context.day_key
        meals = []
    first_meal = (
        profile.category == "meal"
        and context.meal is not None
        and context.meal not in meals
    )
    if first_meal and context.meal is not None:
        meals.append(context.meal)
    if intake.repetitive:
        effect = CareEffect.FOOD_REPEAT
    elif first_meal and context.meal is not None:
        effect = CareEffect.FOOD_MEAL
    else:
        effect = CareEffect.FOOD_SNACK
    return replace(
        result,
        meals_date=meals_date,
        meals_today=tuple(meals),
        food=intake.food,
        needs=replace(
            result.needs,
            satiety=intake.satiety,
            social=clamp_need_value(
                state.social + BALANCE.integer("care", "feed_social_gain")
            ),
        ),
        result=CareResult("feed", effect, selected_food, context.meal),
    )


def resolve_care_time(now: float | None) -> float:
    """Resolve the clock once per interaction for deterministic transitions."""
    return time.time() if now is None else now
