"""Version-one pet save translation, separate from mutable gameplay rules."""

from __future__ import annotations

import math
import time
from datetime import datetime
from typing import Any

from ..pet.balance import BALANCE
from ..pet.food import FOOD_BALANCE, FOOD_CATALOG, FoodState
from ..pet.friendship import (
    CONTACT_ACTIONS,
    FRIENDSHIP_DAILY_CAP,
    LEGACY_REWARD_ACTIONS,
)
from ..pet.friendship_history import FriendshipHistory
from ..pet.routine import MEAL_NAMES
from ..pet.state import PetState
from ..pet.value_rules import bounded_number, clamp_need_value, clamp_saved_time
from .friendship_codec import decode_friendship, encode_friendship, valid_friendship
from .moodlet_codec import decode_moodlets, encode_moodlets
from .sleep_codec import decode_sleep, encode_sleep, valid_sleep
from .wish_codec import decode_wishes, encode_wishes


def decode_pet_state(value: Any, *, now: float | None = None) -> PetState:
    """Load old saves defensively, preserving existing needs and trust."""
    current = time.time() if now is None else now
    if not isinstance(value, dict):
        return PetState(updated_at=current)
    timestamp = value.get("updated_at", current)
    try:
        timestamp = float(timestamp)
    except (TypeError, ValueError, OverflowError):
        timestamp = current
    if not math.isfinite(timestamp):
        timestamp = current
    try:
        datetime.fromtimestamp(timestamp)
    except (ValueError, OSError, OverflowError):
        timestamp = current
    meals = value.get("meals_today")
    if not isinstance(meals, list):
        meals = []
    allowed_meals = tuple(MEAL_NAMES)
    valid_meals = [m for m in allowed_meals if m in meals]
    meals_date = value.get("meals_date", "")
    if not isinstance(meals_date, str) or len(meals_date) != 10:
        meals_date = ""
    sleeping = value.get("sleeping") is True
    origin = value.get("sleep_origin")
    if origin not in ("routine", "manual", "nap", "recovery"):
        origin = "manual" if sleeping else ""
    night_key = value.get("auto_sleep_night")
    if not isinstance(night_key, str) or len(night_key) > 10:
        night_key = ""
    elapsed = _load_lived_seconds(value.get("time"))
    relationship = FriendshipHistory()
    if "relationship" in value and valid_friendship(value["relationship"], elapsed):
        relationship = decode_friendship(value["relationship"], elapsed)
    moodlets = None
    if "moodlets" in value:
        try:
            moodlets = decode_moodlets(value["moodlets"], elapsed)
        except (ValueError, TypeError, OverflowError):
            pass  # Preserve valid care; StateStore backs up the original on save.
    wishes = None
    if "wishes" in value:
        try:
            wishes = decode_wishes(value["wishes"], elapsed)
        except (ValueError, TypeError, OverflowError):
            pass
    return PetState(
        satiety=clamp_need_value(
            value.get("satiety"), BALANCE.number("initial", "satiety")
        ),
        mood=clamp_need_value(value.get("mood"), BALANCE.number("initial", "mood")),
        energy=clamp_need_value(
            value.get("energy"), BALANCE.number("initial", "energy")
        ),
        social=clamp_need_value(
            value.get("social"), BALANCE.number("initial", "social")
        ),
        affection=clamp_need_value(
            value.get("affection"), BALANCE.number("initial", "affection")
        ),
        friendship=clamp_need_value(
            value.get("friendship"), BALANCE.number("initial", "friendship")
        ),
        friendship_day=value.get("friendship_day", "")
        if isinstance(value.get("friendship_day"), str)
        and len(value.get("friendship_day", "")) == 10
        else "",
        friendship_gained_today=min(
            FRIENDSHIP_DAILY_CAP,
            clamp_need_value(value.get("friendship_gained_today", 0.0), 0.0),
        ),
        care_types_today=_load_care_types(value.get("care_types_today")),
        care_last_rewards=_load_reward_times(value.get("care_last_rewards")),
        sleeping=sleeping,
        updated_at=timestamp,
        meals_date=meals_date,
        meals_today=valid_meals,
        sleep_origin=origin,
        auto_sleep_night=night_key,
        nap_until=clamp_saved_time(value.get("nap_until")),
        food=decode_food_state(value.get("food")),
        fun=clamp_need_value(value.get("fun"), BALANCE.number("initial", "fun")),
        auto_nap_day=value.get("auto_nap_day", "")
        if isinstance(value.get("auto_nap_day"), str)
        and len(value.get("auto_nap_day", "")) == 10
        else "",
        lived_seconds=elapsed, relationship=relationship,
        moodlets=moodlets,
        wishes=wishes,
        sleep_episode=decode_sleep(value["sleep_episode"], elapsed)
        if "sleep_episode" in value and valid_sleep(value["sleep_episode"], elapsed)
        else None,
    )


def encode_pet_state(state: PetState) -> dict[str, Any]:
    return {
        "satiety": state.satiety,
        "mood": state.mood,
        "energy": state.energy,
        "social": state.social,
        "affection": state.affection,
        "friendship": state.friendship,
        "friendship_day": state.friendship_day,
        "friendship_gained_today": round(state.friendship_gained_today, 4),
        "care_types_today": list(state.care_types_today),
        "care_last_rewards": dict(state.care_last_rewards),
        "sleeping": state.sleeping,
        "updated_at": state.updated_at,
        "time": {"version": 1, "lived_seconds": state.lived_seconds},
        "relationship": encode_friendship(state.friendship_history),
        "sleep_episode": encode_sleep(state.sleep_episode),
        "moodlets": encode_moodlets(state.moodlets),
        "wishes": encode_wishes(state.wishes),
        "meals_date": state.meals_date,
        "meals_today": list(state.meals_today),
        "sleep_origin": state.sleep_origin,
        "auto_sleep_night": state.auto_sleep_night,
        "nap_until": state.nap_until,
        "auto_nap_day": state.auto_nap_day,
        "food": encode_food_state(state.food),
        "fun": state.fun,
    }


def valid_pet_time(raw: Any) -> bool:
    """Validate the optional elapsed axis without accepting bools or NaNs."""
    structure_valid = (
        isinstance(raw, dict)
        and type(raw.get("version")) is int
        and raw["version"] == 1
        and type(raw.get("lived_seconds")) in (int, float)
    )
    if not structure_valid:
        return False
    try:
        return math.isfinite(raw["lived_seconds"]) and raw["lived_seconds"] >= 0
    except OverflowError:
        return False


def _load_lived_seconds(raw: Any) -> float:
    # Missing/invalid history never claims prior care, activity or neglect.
    return float(raw["lived_seconds"]) if valid_pet_time(raw) else 0.0


def _load_care_types(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [action for action in CONTACT_ACTIONS if action in raw]


def _load_reward_times(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    return {
        action: clamp_saved_time(raw[action])
        for action in (*CONTACT_ACTIONS, *LEGACY_REWARD_ACTIONS)
        if action in raw and clamp_saved_time(raw[action]) > 0
    }


def decode_food_state(raw: Any) -> FoodState:
    """Older save files without food data start with a neutral state."""
    if not isinstance(raw, dict):
        return FoodState()
    foods = raw.get("recent_food_ids", [])
    if not isinstance(foods, list):
        foods = []
    recent = tuple(
        food_id
        for food_id in foods[-FOOD_BALANCE.maximum_recent_foods :]
        if isinstance(food_id, str) and food_id in FOOD_CATALOG
    )
    return FoodState(
        remaining_digest_minutes=bounded_number(
            raw.get("remaining_digest_minutes"),
            0.0,
            FOOD_BALANCE.maximum_digest_reserve_minutes,
        ),
        awake_hours_since_last_food=bounded_number(
            raw.get("awake_hours_since_last_food"),
            0.0,
            1000.0,
        ),
        awake_hours_since_main_meal=bounded_number(
            raw.get("awake_hours_since_main_meal"),
            0.0,
            1000.0,
        ),
        recent_food_ids=recent,
    )


def encode_food_state(state: FoodState) -> dict[str, Any]:
    return {
        "remaining_digest_minutes": round(state.remaining_digest_minutes, 4),
        "awake_hours_since_last_food": round(
            state.awake_hours_since_last_food,
            4,
        ),
        "awake_hours_since_main_meal": round(
            state.awake_hours_since_main_meal,
            4,
        ),
        "recent_food_ids": list(state.recent_food_ids),
    }
