"""Owner-thread selection and bounded, individually warmed API content buffers."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Literal, Protocol

from .social_content import PreparedSocialContent, SocialCategory


@dataclass(frozen=True, slots=True)
class SocialFetchResult:
    token: object
    category: SocialCategory
    content: PreparedSocialContent | None = None


class SocialContentWorker(Protocol):
    def start(self, category: SocialCategory, token: object) -> None: ...

    def poll(self) -> SocialFetchResult | None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class SocialSelection:
    status: Literal["ready", "waiting", "error", "disabled"]
    content: PreparedSocialContent | None = None


class SocialContentCoordinator:
    """Workers return data only; readiness never changes pet needs or rewards."""

    def __init__(self, worker: SocialContentWorker) -> None:
        self._worker = worker
        self._buffers: dict[SocialCategory, deque[PreparedSocialContent]] = {
            category: deque() for category in SocialCategory
        }
        self._enabled = False
        self._closed = False
        self._generation = 0
        self._request: tuple[object, SocialCategory, int] | None = None
        self._waiting: SocialCategory | None = None
        self._offered: PreparedSocialContent | None = None
        self._failed: set[SocialCategory] = set()
        self._recent: deque[PreparedSocialContent] = deque(maxlen=40)

    @property
    def enabled(self) -> bool:
        return self._enabled and not self._closed

    @property
    def waiting(self) -> bool:
        return self._waiting is not None

    def count(self, category: SocialCategory) -> int:
        return len(self._buffers[category])

    def set_enabled(self, enabled: bool) -> None:
        if self._closed or enabled == self._enabled:
            return
        self._generation += 1
        self._enabled = enabled
        self.cancel_selection()
        self._failed.clear()
        for buffer in self._buffers.values():
            buffer.clear()
        self._pump()

    def select(self, category: SocialCategory) -> SocialSelection:
        if not isinstance(category, SocialCategory):
            raise ValueError("Unknown social category")
        self.cancel_selection()
        if not self.enabled:
            return SocialSelection("disabled")
        if self._buffers[category]:
            content = self._buffers[category].popleft()
            self._offered = content
            self._pump()
            return SocialSelection("ready", content)
        self._failed.discard(category)
        self._waiting = category
        self._pump()
        return SocialSelection("waiting")

    def cancel_selection(self) -> None:
        self._waiting = None
        self._offered = None

    def accept(self, content: PreparedSocialContent) -> None:
        """Call once when actual playback is accepted, never while warming."""
        if self._offered is not content:
            raise ValueError("Conversation is no longer offered")
        self._offered = None
        self._recent.append(content)

    def _duplicate(self, item: PreparedSocialContent) -> bool:
        known = (*self._recent, *((self._offered,) if self._offered else ()),
                 *(entry for buffer in self._buffers.values()
                                 for entry in buffer))
        return any(entry.identity == item.identity
                   or entry.fingerprint == item.fingerprint for entry in known)

    def poll(self) -> SocialSelection | None:
        if self._closed:
            return None
        result = self._worker.poll()
        update: SocialSelection | None = None
        if result is not None and self._request is not None:
            token, category, generation = self._request
            if result.token is token:
                self._request = None
                if self.enabled and generation == self._generation:
                    item = result.content
                    if (item is None or result.category != category
                            or item.category != category or self._duplicate(item)):
                        self._failed.add(category)
                        if self._waiting == category:
                            self._waiting = None
                            update = SocialSelection("error")
                    elif self._waiting == category:
                        self._waiting = None
                        self._offered = item
                        update = SocialSelection("ready", item)
                    else:
                        self._buffers[category].append(item)
        self._pump()
        return update

    def _pump(self) -> None:
        if not self.enabled or self._request is not None:
            return
        candidates = [category for category in SocialCategory
                      if self.count(category) < 2 and category not in self._failed]
        if not candidates:
            return
        category = (self._waiting if self._waiting in candidates else
                    min(candidates, key=self.count))
        assert category is not None
        token = object()
        self._request = (token, category, self._generation)
        self._worker.start(category, token)

    def close(self) -> None:
        if self._closed:
            return
        self.set_enabled(False)
        self._closed = True
        self._worker.close()
