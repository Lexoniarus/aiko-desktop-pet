"""Compatibility imports; the canonical implementation lives in pet.mind."""

from ..pet.mind.adaptive import (
    AdaptiveRoutine as AdaptiveRoutine,
    AdaptiveMemory as AdaptiveMemory,
    Behaviour as Behaviour,
    Observation as Observation,
    SLOTS as SLOTS,
    DAILY_DECAY as DAILY_DECAY,
    MAX_OBSERVATION_SECONDS as MAX_OBSERVATION_SECONDS,
    _hours as _hours,
    clamp as clamp,
    ActivityMode as ActivityMode,
    determine_activity_mode as determine_activity_mode,
    determine_sleep_options as determine_sleep_options,
)
