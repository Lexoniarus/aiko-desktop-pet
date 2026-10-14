"""Compatibility imports; the canonical implementation lives in pet.mind."""

from ..pet.mind.adaptive_policy import (
    ActivityMode as ActivityMode,
    SleepOptions as SleepOptions,
    determine_activity_mode as determine_activity_mode,
    determine_sleep_options as determine_sleep_options,
)
