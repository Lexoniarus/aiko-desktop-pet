"""Map core fields into the existing immutable PetValues, without progression.

The caller owns save_state time/revision and the full snapshot transaction.
Wish, Moodlet and relationship mappers retain their separate owned fields.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Collection
from dataclasses import replace
from typing import Any

from ...pet.catalog_validation import number_value
from ...pet.food import FOOD_BALANCE, FOOD_CATALOG, FoodState
from ...pet.friendship import CONTACT_ACTIONS, LEGACY_REWARD_ACTIONS
from ...pet.routine import MEAL_NAMES
from ...pet.state_values import PetValues
from ..sleep_codec import decode_sleep, encode_sleep
from .rows import (
    boolean,
    json_value,
    nonnegative,
    parse_json,
    singleton,
    upsert_singleton,
)

_NEEDS = ("satiety", "energy", "fun", "social", "affection", "mood", "friendship")
_DAYS = ("friendship_day", "meals_date", "auto_sleep_night", "auto_nap_day")
_FOOD_NUMBERS = ("remaining_digest_minutes", "awake_hours_since_last_food",
                 "awake_hours_since_main_meal")
_CORE_FIELDS = (*_NEEDS, *_DAYS, "friendship_gained_today", "nap_until", "sleep_origin")


def _string_list(raw: Any, allowed: Collection[str], maximum: int) -> tuple[str, ...]:
    if (not isinstance(raw, list) or len(raw) > maximum
            or any(not isinstance(v, str) or v not in allowed for v in raw)):
        raise ValueError("Invalid bounded saved list")
    return tuple(raw)


def _core_values(row: dict[str, Any]) -> dict[str, Any]:
    values: dict[str, Any] = {
        key: number_value(row[key], minimum=0, maximum=100, context=key)
        for key in _NEEDS
    }
    for key in _DAYS:
        value = row[key]
        if not isinstance(value, str) or len(value) not in (0, 10):
            raise ValueError("Invalid saved day marker")
        values[key] = value
    for key in ("friendship_gained_today", "nap_until"):
        values[key] = nonnegative(row[key], key)
    if row["sleep_origin"] not in ("", "routine", "manual", "nap", "recovery"):
        raise ValueError("Invalid saved sleep origin")
    values["sleep_origin"] = row["sleep_origin"]
    values["sleeping"] = boolean(row["sleeping"])
    values["care_types_today"] = _string_list(
        parse_json(row["care_types_today"]), CONTACT_ACTIONS, len(CONTACT_ACTIONS),
    )
    values["meals_today"] = _string_list(
        parse_json(row["meals_today"]), MEAL_NAMES, len(MEAL_NAMES),
    )
    rewards = parse_json(row["care_last_rewards"])
    if not isinstance(rewards, dict) or any(
        key not in (*CONTACT_ACTIONS, *LEGACY_REWARD_ACTIONS) for key in rewards
    ):
        raise ValueError("Invalid saved legacy reward anchors")
    values["care_last_rewards"] = tuple(
        (key, nonnegative(value, "legacy reward time"))
        for key, value in rewards.items()
    )
    values["food"] = FoodState(
        **{key: nonnegative(row[key], key) for key in _FOOD_NUMBERS},
        recent_food_ids=_string_list(parse_json(row["recent_food_ids"]), FOOD_CATALOG,
                                     FOOD_BALANCE.maximum_recent_foods),
    )
    return values


def write_pet_core(connection: sqlite3.Connection, snapshot: PetValues) -> None:
    anchor = singleton(connection, "save_state")
    if (snapshot.updated_at, snapshot.lived_seconds) != (
        anchor["updated_at"], anchor["lived_seconds"],
    ):
        raise ValueError("Pet values do not belong to this save checkpoint")
    row = {key: getattr(snapshot, key) for key in _CORE_FIELDS}
    row.update(
        sleeping=int(snapshot.sleeping),
        care_types_today=json_value(snapshot.care_types_today),
        care_last_rewards=json_value(dict(snapshot.care_last_rewards)),
        meals_today=json_value(snapshot.meals_today),
        recent_food_ids=json_value(snapshot.food.recent_food_ids),
        **{key: getattr(snapshot.food, key) for key in _FOOD_NUMBERS},
    )
    _core_values(row)
    sleep = encode_sleep(snapshot.sleep_episode)
    decode_sleep(sleep, snapshot.lived_seconds)
    del sleep["version"]
    sleep["care_break"] = int(snapshot.sleep_episode.care_break)
    sleep["food_failed"] = int(snapshot.sleep_episode.food_failed)
    sleep["failed_food_sources"] = json_value(
        snapshot.sleep_episode.failed_food_sources
    )
    upsert_singleton(connection, "pet_state", row)
    upsert_singleton(connection, "sleep_state", sleep)


def read_pet_core(connection: sqlite3.Connection, template: PetValues) -> PetValues:
    """Replace only owned fields; later mappers assemble the same checkpoint."""
    anchor = singleton(connection, "save_state")
    elapsed = nonnegative(anchor["lived_seconds"], "lived time")
    sleep = singleton(connection, "sleep_state")
    del sleep["id"]
    sleep.update(version=1, care_break=boolean(sleep["care_break"]),
                 food_failed=boolean(sleep["food_failed"]),
                 failed_food_sources=parse_json(sleep["failed_food_sources"]))
    return replace(
        template, **_core_values(singleton(connection, "pet_state")),
        updated_at=nonnegative(anchor["updated_at"], "UTC checkpoint"),
        lived_seconds=elapsed, sleep_episode=decode_sleep(sleep, elapsed),
    )
