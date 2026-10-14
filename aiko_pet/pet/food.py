"""Food-only hunger, digestion and meal variety rules.

All balance knobs are in FOOD_BALANCE and FOOD_CATALOG below. These rules
know nothing about Tk, Windows input readers, dialogue or the other needs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Literal

from .value_rules import clamp_need_value

FoodId = Literal["onigiri", "sandwich", "taiyaki", "apple", "dango"]
FoodCategory = Literal["meal", "snack"]


@dataclass(frozen=True, slots=True)
class FoodBalance:
    """Hours, minutes and 0..1 rates make gameplay tuning readable."""

    awake_hunger_points_per_hour: float = 8.0
    sleeping_hunger_points_per_hour: float = 1.4
    maximum_hardware_hunger_bonus: float = 0.20
    maximum_user_input_hunger_bonus: float = 0.18
    maximum_combined_activity_bonus: float = 0.35
    awake_hours_before_hunger_accelerates: float = 3.0
    additional_hunger_fraction_per_hour_without_food: float = 0.055
    maximum_long_fast_hunger_bonus: float = 0.25
    maximum_digest_hunger_reduction: float = 0.55
    digest_minutes_for_full_hunger_reduction: float = 80.0
    maximum_digest_reserve_minutes: float = 175.0
    digestion_speedup_from_activity: float = 0.6
    digestion_speed_during_sleep: float = 0.3
    internal_simulation_step_minutes: float = 5.0
    consecutive_repeats_before_dislike: int = 2
    repeated_food_mood_penalty: float = 6.0
    maximum_recent_foods: int = 8
    too_full_to_eat_threshold: float = 96.0


FOOD_BALANCE = FoodBalance()


@dataclass(frozen=True, slots=True)
class FoodProfile:
    """Easy-to-edit effects of one of Aiko's five food assets."""

    id: FoodId
    display_name: str
    category: FoodCategory
    instant_satiety_points: float
    digest_reserve_minutes: float
    normal_mood_bonus: float


FOOD_CATALOG: dict[FoodId, FoodProfile] = {
    "onigiri": FoodProfile("onigiri", "Onigiri", "meal", 30.0, 105.0, 4.0),
    "sandwich": FoodProfile("sandwich", "Sandwich", "meal", 38.0, 145.0, 5.0),
    "taiyaki": FoodProfile("taiyaki", "Taiyaki", "snack", 20.0, 55.0, 4.0),
    "apple": FoodProfile("apple", "Apfel", "snack", 14.0, 38.0, 3.0),
    "dango": FoodProfile("dango", "Dango", "snack", 10.0, 20.0, 2.0),
}
DEFAULT_FOOD_ID: FoodId = "onigiri"


def _bounded_number(raw: Any, default: float, maximum: float) -> float:
    if type(raw) not in (int, float):
        return default
    number = float(raw)
    if not math.isfinite(number):
        return default
    return max(0.0, min(maximum, number))


@dataclass(frozen=True, slots=True)
class FoodActivity:
    """Observed work, never guessed task identity or unseen user activity."""

    hardware_load: float = 0.0
    user_input_activity: float = 0.0


@dataclass(frozen=True, slots=True)
class FoodState:
    """Session-progressing nutrition state, serialized with the pet."""

    remaining_digest_minutes: float = 0.0
    awake_hours_since_last_food: float = 0.0
    awake_hours_since_main_meal: float = 0.0
    recent_food_ids: tuple[FoodId, ...] = ()

    @property
    def last_food_id(self) -> FoodId | None:
        return self.recent_food_ids[-1] if self.recent_food_ids else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "remaining_digest_minutes": round(self.remaining_digest_minutes, 4),
            "awake_hours_since_last_food": round(
                self.awake_hours_since_last_food, 4,
            ),
            "awake_hours_since_main_meal": round(
                self.awake_hours_since_main_meal, 4,
            ),
            "recent_food_ids": list(self.recent_food_ids),
        }

    @classmethod
    def from_dict(cls, raw: Any) -> FoodState:
        """Older save files without food data start with a neutral state."""
        if not isinstance(raw, dict):
            return cls()
        foods = raw.get("recent_food_ids", [])
        if not isinstance(foods, list):
            foods = []
        recent = tuple(
            food_id for food_id in foods[-FOOD_BALANCE.maximum_recent_foods:]
            if isinstance(food_id, str) and food_id in FOOD_CATALOG
        )
        return cls(
            remaining_digest_minutes=_bounded_number(
                raw.get("remaining_digest_minutes"), 0.0,
                FOOD_BALANCE.maximum_digest_reserve_minutes,
            ),
            awake_hours_since_last_food=_bounded_number(
                raw.get("awake_hours_since_last_food"), 0.0, 1000.0,
            ),
            awake_hours_since_main_meal=_bounded_number(
                raw.get("awake_hours_since_main_meal"), 0.0, 1000.0,
            ),
            recent_food_ids=recent,  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class FoodIntake:
    """One food selection's immediate, atomic domain outcome."""

    accepted: bool
    satiety: float
    mood_change: float
    food: FoodState
    repetitive: bool


@dataclass(frozen=True, slots=True)
class FoodProgress:
    """Both hunger and the remaining digestive effect after elapsed time."""

    satiety: float
    food: FoodState


def is_repeated_food(food: FoodState, food_id: FoodId) -> bool:
    """Dislike starts after consecutive identical servings, not one repeat."""
    threshold = FOOD_BALANCE.consecutive_repeats_before_dislike
    return (
        len(food.recent_food_ids) >= threshold
        and all(item == food_id for item in food.recent_food_ids[-threshold:])
    )


def eat_food(
    food: FoodState, current_satiety: float, food_id: FoodId,
) -> FoodIntake:
    """Add satiety and digest reserve; a snack does not count as a full meal."""
    profile = FOOD_CATALOG[food_id]
    if current_satiety >= FOOD_BALANCE.too_full_to_eat_threshold:
        return FoodIntake(False, current_satiety, 0.0, food, False)
    repetitive = is_repeated_food(food, food_id)
    history = (*food.recent_food_ids, food_id)
    updated = replace(
        food,
        remaining_digest_minutes=min(
            FOOD_BALANCE.maximum_digest_reserve_minutes,
            food.remaining_digest_minutes + profile.digest_reserve_minutes,
        ),
        awake_hours_since_last_food=0.0,
        awake_hours_since_main_meal=(
            0.0 if profile.category == "meal"
            else food.awake_hours_since_main_meal
        ),
        recent_food_ids=history[-FOOD_BALANCE.maximum_recent_foods:],
    )
    mood_change = profile.normal_mood_bonus - (
        FOOD_BALANCE.repeated_food_mood_penalty if repetitive else 0.0
    )
    return FoodIntake(
        accepted=True,
        satiety=clamp_need_value(
            current_satiety + profile.instant_satiety_points,
        ),
        mood_change=mood_change,
        food=updated,
        repetitive=repetitive,
    )


def hunger_activity_multiplier(activity: FoodActivity) -> float:
    """CPU/GPU/RAM work and real user inputs each add bounded hunger."""
    hardware = _bounded_number(activity.hardware_load, 0.0, 1.0)
    user = _bounded_number(activity.user_input_activity, 0.0, 1.0)
    bonus = min(
        FOOD_BALANCE.maximum_combined_activity_bonus,
        hardware * FOOD_BALANCE.maximum_hardware_hunger_bonus
        + user * FOOD_BALANCE.maximum_user_input_hunger_bonus,
    )
    return 1.0 + bonus


def hunger_after_long_food_break(awake_hours_since_food: float) -> float:
    """Late hunger increases gently and stops increasing at a fixed cap."""
    overdue = max(
        0.0,
        awake_hours_since_food
        - FOOD_BALANCE.awake_hours_before_hunger_accelerates,
    )
    return 1.0 + min(
        FOOD_BALANCE.maximum_long_fast_hunger_bonus,
        overdue * FOOD_BALANCE.additional_hunger_fraction_per_hour_without_food,
    )


def digestion_hunger_multiplier(remaining_minutes: float) -> float:
    """Nutrition slows decay progressively until the reserve is exhausted."""
    fullness = min(
        1.0,
        max(0.0, remaining_minutes)
        / FOOD_BALANCE.digest_minutes_for_full_hunger_reduction,
    )
    return 1.0 - FOOD_BALANCE.maximum_digest_hunger_reduction * fullness


def advance_food(
    food: FoodState, satiety: float, hours: float, *,
    sleeping: bool, activity: FoodActivity | None = None,
) -> FoodProgress:
    """Integrate digestion and hunger in five-minute steps, not once per tick.

    All input time comes from the host's *active session clock*. This method
    never computes the gap from wall timestamps after a program restart.
    """
    if not math.isfinite(hours) or hours <= 0.0:
        return FoodProgress(satiety, food)
    observed = activity if activity is not None else FoodActivity()
    activity_multiplier = hunger_activity_multiplier(observed)
    remainder = hours
    result = food
    hunger = satiety
    step_limit = FOOD_BALANCE.internal_simulation_step_minutes / 60.0
    while remainder > 1e-9:
        step = min(step_limit, remainder)
        if sleeping:
            rate = FOOD_BALANCE.sleeping_hunger_points_per_hour
            digestion_speed = FOOD_BALANCE.digestion_speed_during_sleep
            result = replace(
                result,
                remaining_digest_minutes=max(
                    0.0, result.remaining_digest_minutes
                    - step * 60.0 * digestion_speed,
                ),
            )
        else:
            rate = (
                FOOD_BALANCE.awake_hunger_points_per_hour
                * activity_multiplier
                * hunger_after_long_food_break(
                    result.awake_hours_since_last_food,
                )
                * digestion_hunger_multiplier(
                    result.remaining_digest_minutes,
                )
            )
            digestion_speed = (
                1.0 + FOOD_BALANCE.digestion_speedup_from_activity
                * (activity_multiplier - 1.0)
            )
            result = replace(
                result,
                remaining_digest_minutes=max(
                    0.0, result.remaining_digest_minutes
                    - step * 60.0 * digestion_speed,
                ),
                awake_hours_since_last_food=(
                    result.awake_hours_since_last_food + step
                ),
                awake_hours_since_main_meal=(
                    result.awake_hours_since_main_meal + step
                ),
            )
        hunger = clamp_need_value(hunger - step * rate)
        remainder -= step
    return FoodProgress(hunger, result)
