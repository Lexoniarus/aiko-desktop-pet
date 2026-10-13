"""Legacy PetState module; canonical aggregate lives in aiko_pet.pet.state."""

from __future__ import annotations

from .pet.state import (
    PetState as PetState,
    CARE_FRIENDSHIP_GAIN as CARE_FRIENDSHIP_GAIN,
    CARE_PRIMARY_NEED as CARE_PRIMARY_NEED,
    FRIENDSHIP_DAILY_CAP as FRIENDSHIP_DAILY_CAP,
    FRIENDSHIP_NEED_THRESHOLD as FRIENDSHIP_NEED_THRESHOLD,
    FRIENDSHIP_REWARD_INTERVAL as FRIENDSHIP_REWARD_INTERVAL,
    FRIENDSHIP_VARIETY_BONUS as FRIENDSHIP_VARIETY_BONUS,
    LEGACY_REWARD_ACTIONS as LEGACY_REWARD_ACTIONS,
    MAX_CATCHUP_SECONDS as MAX_CATCHUP_SECONDS,
    MAX_LIVE_EFFORT_SECONDS as MAX_LIVE_EFFORT_SECONDS,
    SIMULATION_STEP_SECONDS as SIMULATION_STEP_SECONDS,
    apply_care_action as apply_care_action,
    award_friendship_for_care as award_friendship_for_care,
    apply_need_decay as apply_need_decay,
    advance_pet_time as advance_pet_time,
    apply_daily_routine as apply_daily_routine,
    bounded as bounded,
    clamp_saved_time as clamp_saved_time,
    MEAL_NAMES as MEAL_NAMES,
    TimeContext as TimeContext,
)
