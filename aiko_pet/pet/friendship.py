"""Pure friendship reward policy; PetState owns all reward mutations."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from .routine import context_at
from .value_rules import clamp_need_value

FRIENDSHIP_REWARD_INTERVAL = 12 * 60
FRIENDSHIP_DAILY_CAP = 5.0
# Only care addressing a genuine need can slowly build the relationship.
CARE_FRIENDSHIP_GAIN = {
    "feed": 0.9, "play": 1.0, "pet": 1.0, "talk": 1.0,
}
CARE_PRIMARY_NEED = {
    "feed": "satiety", "play": "fun",
    "pet": "affection", "talk": "social",
}
FRIENDSHIP_NEED_THRESHOLD = 80.0
FRIENDSHIP_VARIETY_BONUS = 0.35
# Keep legacy history during migration, but these no longer earn friendship.
LEGACY_REWARD_ACTIONS = ("energy_drink", "sleep")


class FriendshipRecord(Protocol):
    """Readable relationship fields needed to evaluate a care reward."""

    friendship: float
    friendship_day: str
    friendship_gained_today: float
    care_types_today: list[str]
    care_last_rewards: dict[str, float]


@dataclass(frozen=True, slots=True)
class FriendshipTransition:
    """Complete immutable result of one eligible friendship evaluation."""

    friendship: float
    day: str
    gained_today: float
    care_types: tuple[str, ...]
    last_rewards: tuple[tuple[str, float], ...]


def calculate_friendship_reward(
    record: FriendshipRecord,
    action: str,
    stamp: float,
    need_before: float,
) -> FriendshipTransition | None:
    """Decide new relationship values without mutating a record."""
    if (
        action not in CARE_FRIENDSHIP_GAIN
        or not math.isfinite(stamp) or stamp <= 0
    ):
        return None
    context = context_at(stamp)
    day = record.friendship_day
    gained = record.friendship_gained_today
    types = list(record.care_types_today)
    rewards = dict(record.care_last_rewards)
    friendship = record.friendship
    if day != context.day_key:
        day = context.day_key
        gained = 0.0
        types = []
    if need_before <= FRIENDSHIP_NEED_THRESHOLD:
        last = rewards.get(action)
        if last is None or stamp - last >= FRIENDSHIP_REWARD_INTERVAL:
            remaining = max(0.0, FRIENDSHIP_DAILY_CAP - gained)
            first_time = action not in types
            variety = (
                FRIENDSHIP_VARIETY_BONUS
                if first_time and types else 0.0
            )
            gain = min(
                remaining, CARE_FRIENDSHIP_GAIN[action] + variety,
                100.0 - friendship,
            )
            if gain > 0:
                friendship = clamp_need_value(friendship + gain)
                gained += gain
                rewards[action] = stamp
                if first_time:
                    types.append(action)
    return FriendshipTransition(
        friendship=friendship,
        day=day,
        gained_today=gained,
        care_types=tuple(types),
        last_rewards=tuple(rewards.items()),
    )


