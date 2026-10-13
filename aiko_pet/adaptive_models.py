"""Legacy adaptive data imports; see personality.adaptive_models."""

from __future__ import annotations

from .personality.adaptive_models import (
    Observation as Observation,
    AdaptiveMemory as AdaptiveMemory,
    Behaviour as Behaviour,
    ActivityMode as ActivityMode,
    SLOTS as SLOTS,
    DAILY_DECAY as DAILY_DECAY,
    MAX_OBSERVATION_SECONDS as MAX_OBSERVATION_SECONDS,
    clamp as clamp,
    _hours as _hours,
)
