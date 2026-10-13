"""Bounded thread-safe notification ingress; no Tk calls or network server."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from threading import Lock
from typing import Literal, TypeAlias

from .events import IncomingNotification

SubmissionStatus: TypeAlias = Literal["accepted", "duplicate", "full"]


@dataclass(frozen=True, slots=True)
class NotificationReceipt:
    """Acknowledgement for a future transport adapter to map to HTTP status."""

    event_id: str
    status: SubmissionStatus


class NotificationInbox:
    """Accept data from any thread and drain it only on the application thread.

    A small recent-ID cache prevents simple retries from displaying duplicates.
    When full, reject new items instead of blocking or silently dropping them.
    """

    def __init__(
        self, *, capacity: int = 32, recent_capacity: int = 128,
    ) -> None:
        if capacity < 1 or recent_capacity < 1:
            raise ValueError("Inbox capacities must be positive")
        self._capacity = capacity
        self._recent_capacity = recent_capacity
        self._pending: deque[IncomingNotification] = deque()
        self._pending_ids: set[str] = set()
        self._recent: deque[str] = deque()
        self._recent_ids: set[str] = set()
        self._lock = Lock()
        self._closed = False

    def submit(self, notification: IncomingNotification) -> NotificationReceipt:
        """Nonblocking, bounded and idempotent notification submission."""
        with self._lock:
            if self._closed:
                return NotificationReceipt(notification.event_id, "full")
            if (
                notification.event_id in self._pending_ids
                or notification.event_id in self._recent_ids
            ):
                return NotificationReceipt(notification.event_id, "duplicate")
            if len(self._pending) >= self._capacity:
                return NotificationReceipt(notification.event_id, "full")
            self._pending.append(notification)
            self._pending_ids.add(notification.event_id)
            return NotificationReceipt(notification.event_id, "accepted")

    def pop_next(self) -> IncomingNotification | None:
        """Remove one accepted event in arrival order, retaining its ID."""
        with self._lock:
            if not self._pending:
                return None
            notification = self._pending.popleft()
            self._pending_ids.remove(notification.event_id)
            if len(self._recent) >= self._recent_capacity:
                previous = self._recent.popleft()
                self._recent_ids.remove(previous)
            self._recent.append(notification.event_id)
            self._recent_ids.add(notification.event_id)
            return notification

    def close(self) -> None:
        """Prevent submissions after shutdown without touching the display."""
        with self._lock:
            self._closed = True
            self._pending.clear()
            self._pending_ids.clear()
