"""Strict v1 pet import, retaining the runtime reader's older-field defaults.

Only absent fields receive defaults. Present histories use their strict owners;
core values must survive the legacy decoder unchanged, with no coercion/clamp.
"""

from dataclasses import asdict, replace
from typing import Any

from ..pet.catalog_validation import number_value, object_fields
from ..pet.friendship import CONTACT_ACTIONS, LEGACY_REWARD_ACTIONS
from ..pet.routine import MEAL_NAMES
from ..pet.state import PetState
from .friendship_codec import decode_friendship
from .moodlet_codec import decode_moodlets
from .pet_codec import decode_pet_state, encode_pet_state, valid_pet_time
from .sleep_codec import decode_sleep
from .wish_codec import decode_wishes

_NEEDS = ("satiety", "mood", "energy", "social", "affection", "friendship", "fun")
_HISTORIES = ("relationship", "sleep_episode", "moodlets", "wishes")


def decode_legacy_pet(raw: Any, *, now: float) -> PetState:
    fields = encode_pet_state(PetState(updated_at=now))
    row = object_fields(raw, (), optional=fields, context="legacy pet")
    if "time" in row:
        object_fields(row["time"], ("version", "lived_seconds"), context="pet time")
        if not valid_pet_time(row["time"]):
            raise ValueError("Invalid legacy pet time")
    elapsed = float(row.get("time", {}).get("lived_seconds", 0))
    for key, decode in (
        ("relationship", decode_friendship), ("sleep_episode", decode_sleep),
        ("moodlets", decode_moodlets), ("wishes", decode_wishes),
    ):
        if key in row:
            decode(row[key], elapsed)
    for key in (*_NEEDS, "updated_at", "friendship_gained_today", "nap_until"):
        if key in row:
            number_value(row[key], minimum=0, maximum=float("inf"), context=key)
    if "sleeping" in row and type(row["sleeping"]) is not bool:
        raise ValueError("Invalid legacy sleeping flag")

    # Lists represent sets in the old reader. Validate members, then retain the
    # original order rather than silently filtering or canonicalizing input.
    lists: dict[str, Any] = {}
    for key, allowed in (("care_types_today", CONTACT_ACTIONS),
                         ("meals_today", MEAL_NAMES)):
        if key in row:
            values = row[key]
            if (not isinstance(values, list)
                    or any(not isinstance(v, str) or v not in allowed for v in values)
                    or len(set(values)) != len(values)):
                raise ValueError(f"Invalid legacy {key}")
            lists[key] = tuple(values)
    rewards = row.get("care_last_rewards", {})
    object_fields(rewards, (), optional=(*CONTACT_ACTIONS, *LEGACY_REWARD_ACTIONS),
                  context="legacy reward anchors")
    for value in rewards.values():
        number_value(value, minimum=0, maximum=4_000_000_000, context="reward time")

    food = row.get("food", {})
    object_fields(food, (), optional=fields["food"], context="legacy food")
    for key, value in food.items():
        if key != "recent_food_ids":
            number_value(value, minimum=0, maximum=float("inf"), context=key)

    pet = decode_pet_state(row, now=now)
    normalized = encode_pet_state(pet)
    # The authored JSON writer rounds these values; import must not do so.
    normalized["friendship_gained_today"] = pet.friendship_gained_today
    normalized["food"] = {**asdict(pet.food),
                          "recent_food_ids": list(pet.food.recent_food_ids)}
    for key, value in row.items():
        if key in (*_HISTORIES, "time", "care_last_rewards", *lists):
            continue
        if key == "food":
            unchanged = all(normalized[key][k] == v for k, v in food.items())
        else:
            unchanged = normalized[key] == value
        if not unchanged:
            raise ValueError(f"Legacy pet field would be normalized or lost: {key}")
    pet.restore_checkpoint(replace(
        pet.capture_checkpoint(), **lists,
        care_last_rewards=tuple((k, float(v)) for k, v in rewards.items()),
    ))
    return pet
