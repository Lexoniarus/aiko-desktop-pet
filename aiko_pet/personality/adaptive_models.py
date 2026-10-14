"""Compatibility imports; the canonical implementation lives in pet.mind."""

from ..pet.mind.adaptive_models import (
    SLOTS as SLOTS,
    MAX_OBSERVATION_SECONDS as MAX_OBSERVATION_SECONDS,
    DAILY_DECAY as DAILY_DECAY,
    clamp as clamp,
    _hours as _hours,
    Observation as Observation,
    AdaptiveMemory as AdaptiveMemory,
    Behaviour as Behaviour,
    ActivityMode as ActivityMode,
)
