"""Data-only contracts for future browser and application notifications.

An integration adapter must authenticate the sender before constructing these
events. The sender identity is injected, never trusted from submitted JSON.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Mapping, TypeAlias

NotificationPriority: TypeAlias = Literal["low", "normal", "high"]
_NOTIFICATION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*\Z")


def _validate_text(name: str, text: str, maximum: int) -> None:
    if not isinstance(text, str):
        raise ValueError(f"{name} must be text")
    if not text.strip() or len(text) > maximum:
        raise ValueError(f"{name} must contain 1 to {maximum} characters")
    if any(ord(char) < 32 and char not in "\t\n" for char in text):
        raise ValueError(f"{name} contains control characters")


@dataclass(frozen=True, slots=True)
class IncomingNotification:
    """Versioned notification data; never a command to run arbitrary code."""

    event_id: str
    source: str
    title: str
    message: str
    priority: NotificationPriority = "normal"
    version: int = 1

    def __post_init__(self) -> None:
        if type(self.version) is not int or self.version != 1:
            raise ValueError("Unsupported notification contract version")
        if (
            not isinstance(self.event_id, str)
            or len(self.event_id) > 96
            or _NOTIFICATION_ID.fullmatch(self.event_id) is None
        ):
            raise ValueError("Invalid notification event ID")
        _validate_text("source", self.source, 80)
        _validate_text("title", self.title, 96)
        _validate_text("message", self.message, 480)
        if self.priority not in ("low", "normal", "high"):
            raise ValueError("Unsupported notification priority")

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, object], *, authenticated_source: str,
    ) -> IncomingNotification:
        """Validate a transport-agnostic payload and bind trusted provenance.

        HTTP requests, WebSocket frames and local IPC can all use this schema.
        Authorization, rate limits and origin checks belong to their adapters.
        """
        allowed = {"version", "type", "id", "title", "message", "priority"}
        if set(payload) - allowed:
            raise ValueError("Unknown notification payload fields")
        if payload.get("version") != 1 or type(payload.get("version")) is not int:
            raise ValueError("Unsupported notification contract version")
        if payload.get("type") != "notification.created":
            raise ValueError("Unsupported event type")
        identifier = payload.get("id")
        title = payload.get("title")
        message = payload.get("message")
        priority = payload.get("priority", "normal")
        if (
            not isinstance(identifier, str)
            or not isinstance(title, str)
            or not isinstance(message, str)
            or not isinstance(priority, str)
        ):
            raise ValueError("Notification fields must be text")
        if priority == "low":
            normalized_priority: NotificationPriority = "low"
        elif priority == "normal":
            normalized_priority = "normal"
        elif priority == "high":
            normalized_priority = "high"
        else:
            raise ValueError("Unsupported notification priority")
        return cls(
            event_id=identifier,
            source=authenticated_source,
            title=title,
            message=message,
            priority=normalized_priority,
        )
