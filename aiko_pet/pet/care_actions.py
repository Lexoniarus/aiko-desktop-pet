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
from .friendship import CARE_PRIMARY_NEED
from .need_decay import NeedLevels
from .routine import context_at
from .value_rules import clamp_need_value


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
    def mood(self) -> float: ...

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


@dataclass(frozen=True, slots=True)
class CareTransition:
    """A validated full snapshot of one care action's intended changes."""

    result: CareResult
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
            state.mood,
            state.energy,
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
            reward_action="energy_drink", need_before=state.energy,
        )
    need_before = float(getattr(state, CARE_PRIMARY_NEED[action]))
    result = replace(
        unchanged,
        changed=True,
        sleeping=sleeping,
        sleep_origin=sleep_origin,
        nap_until=nap_until,
        auto_sleep_night=night_key,
        reward_action=action,
        need_before=need_before,
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
            result=CareResult("pet", CareEffect.AFFECTION),
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
