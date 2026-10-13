"""Legacy friendship policy imports; canonical rules are in pet.friendship."""

from __future__ import annotations

from .pet.friendship import (
    CARE_FRIENDSHIP_GAIN as CARE_FRIENDSHIP_GAIN,
    CARE_PRIMARY_NEED as CARE_PRIMARY_NEED,
    FRIENDSHIP_REWARD_INTERVAL as FRIENDSHIP_REWARD_INTERVAL,
    FRIENDSHIP_DAILY_CAP as FRIENDSHIP_DAILY_CAP,
    FRIENDSHIP_NEED_THRESHOLD as FRIENDSHIP_NEED_THRESHOLD,
    FRIENDSHIP_VARIETY_BONUS as FRIENDSHIP_VARIETY_BONUS,
    LEGACY_REWARD_ACTIONS as LEGACY_REWARD_ACTIONS,
    FriendshipRecord as FriendshipRecord,
    FriendshipTransition as FriendshipTransition,
    calculate_friendship_reward as calculate_friendship_reward,
    award_friendship_for_care as award_friendship_for_care,
)
