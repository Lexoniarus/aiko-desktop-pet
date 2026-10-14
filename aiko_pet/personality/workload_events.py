"""Compatibility imports; the canonical implementation lives in pet.mind."""

import random as random

from ..pet.mind.workload_events import (
    WorkloadEventDetector as WorkloadEventDetector,
    ComputerSnapshot as ComputerSnapshot,
    workload_intensity as workload_intensity,
)
