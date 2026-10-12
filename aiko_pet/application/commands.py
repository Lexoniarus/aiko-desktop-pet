"""Typed commands accepted by Aiko's application layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, cast

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

    @classmethod
    def from_action(cls, action: str) -> CareCommand:
        """Check a UI string before converting it to a typed care command."""
        if action not in CARE_ACTIONS:
            raise ValueError(f"Unsupported care action: {action}")
        return cls(cast(CareAction, action))



@dataclass(frozen=True, slots=True)
class NotificationCommand:
    """An already validated, authorized notification from an adapter."""

    notification: IncomingNotification


ApplicationCommand: TypeAlias = CareCommand | NotificationCommand
