"""Explicit consumption origin, independent of item presentation or custody."""

from enum import StrEnum


class ConsumptionOrigin(StrEnum):
    HANDOVER = "handover"
    AUTONOMOUS = "autonomous"
