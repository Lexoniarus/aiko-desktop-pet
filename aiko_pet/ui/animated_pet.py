"""Compatibility imports for the canonical pet-view sprite renderer."""

import time as time  # Preserve legacy tests patching the shared monotonic clock.

from .pet_view.animated_pet import (
    ActivityReadings as ActivityReadings,
    AnimatedPet as AnimatedPet,
    AnimatedPorts as AnimatedPorts,
    BusyReading as BusyReading,
    CareVisuals as CareVisuals,
    CharacterSettings as CharacterSettings,
    FocusReadings as FocusReadings,
    FocusState as FocusState,
)
