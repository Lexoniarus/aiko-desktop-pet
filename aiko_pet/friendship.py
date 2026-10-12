"""Friendship reward policy with no GUI or persistence dependencies."""

from __future__ import annotations

import math
from typing import Protocol

from .routine import context_at
from .value_rules import bounded

FRIENDSHIP_REWARD_INTERVAL = 12 * 60
FRIENDSHIP_DAILY_CAP = 5.0
# Only care addressing a genuine need can slowly build the relationship.
CARE_FRIENDSHIP_GAIN = {
    "feed": 0.9, "play": 1.0, "pet": 1.0, "talk": 1.0,
}
CARE_PRIMARY_NEED = {
    "feed": "satiety", "play": "mood",
    "pet": "affection", "talk": "social",
}
FRIENDSHIP_NEED_THRESHOLD = 80.0
FRIENDSHIP_VARIETY_BONUS = 0.35
# Keep legacy history during migration, but these no longer earn friendship.
LEGACY_REWARD_ACTIONS = ("energy_drink", "sleep")


class FriendshipRecord(Protocol):
    """Mutable fields that the reward policy needs from a relationship."""

    friendship: float
    friendship_day: str
    friendship_gained_today: float
    care_types_today: list[str]
    care_last_rewards: dict[str, float]


def award_friendship_for_care(
    record: FriendshipRecord,
    action: str,
    stamp: float,
    need_before: float,
) -> None:
    """Reward diverse, useful care, never repeated clicks on full needs."""
    if (action not in CARE_FRIENDSHIP_GAIN or not math.isfinite(stamp)
            or stamp <= 0):
        return
    context = context_at(stamp)
    if record.friendship_day != context.day_key:
        record.friendship_day = context.day_key
        record.friendship_gained_today = 0.0
        record.care_types_today = []
    if need_before > FRIENDSHIP_NEED_THRESHOLD:
        return
    last = record.care_last_rewards.get(action)
    if last is not None and stamp - last < FRIENDSHIP_REWARD_INTERVAL:
        # Also reject a backwards-running system clock for this action.
        return
    remaining = max(0.0, FRIENDSHIP_DAILY_CAP - record.friendship_gained_today)
    first_time = action not in record.care_types_today
    variety = (
        FRIENDSHIP_VARIETY_BONUS
        if first_time and record.care_types_today else 0.0
    )
    gain = min(
        remaining, CARE_FRIENDSHIP_GAIN[action] + variety,
        100.0 - record.friendship,
    )
    if gain <= 0:
        return
    record.friendship = bounded(record.friendship + gain)
    record.friendship_gained_today += gain
    record.care_last_rewards[action] = stamp
    if first_time:
        record.care_types_today.append(action)
