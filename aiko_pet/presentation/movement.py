"""Compatibility imports; pure walking policies belong to pet.movement."""

import random as random  # Existing tests patch the shared RNG via this path.

from ..pet.movement import (
    RandomWalkPlanner as RandomWalkPlanner,
    WalkConditions as WalkConditions,
    WalkController as WalkController,
    WalkStep as WalkStep,
)
