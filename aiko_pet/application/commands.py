"""Typed commands accepted by Aiko's application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from .events import IncomingNotification

CareAction: TypeAlias = Literal[
    "feed", "play", "pet", "talk", "energy_drink", "sleep",
]
CARE_ACTIONS: frozenset[str] = frozenset(
    ("feed", "play", "pet", "talk", "energy_drink", "sleep")
)


@dataclass(frozen=True, slots=True)
class CareCommand:
    """An intentional local care action, never an untrusted API event."""

    action: CareAction

    def __post_init__(self) -> None:
        if self.action not in CARE_ACTIONS:
            raise ValueError(f"Unsupported care action: {self.action}")


@dataclass(frozen=True, slots=True)
class NotificationCommand:
    """An already validated, authorized notification from an adapter."""

    notification: IncomingNotification


ApplicationCommand: TypeAlias = CareCommand | NotificationCommand
