"""Legacy adaptive observation exports; canonical code lives in personality."""

from __future__ import annotations

from .personality.adaptive import (
    AdaptiveRoutine as AdaptiveRoutine,
    AdaptiveMemory as AdaptiveMemory,
    Behaviour as Behaviour,
    Observation as Observation,
    ActivityMode as ActivityMode,
    DAILY_DECAY as DAILY_DECAY,
    MAX_OBSERVATION_SECONDS as MAX_OBSERVATION_SECONDS,
    SLOTS as SLOTS,
    _hours as _hours,
    clamp as clamp,
    determine_activity_mode as determine_activity_mode,
    determine_sleep_options as determine_sleep_options,
)
from .pet.routine import TimeContext as TimeContext, context_at as context_at
