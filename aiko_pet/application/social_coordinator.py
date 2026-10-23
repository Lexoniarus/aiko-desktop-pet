"""One owner-thread scheduler, mixed Sprueche stock and persistent request caps."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, replace
from typing import Callable, Literal, Protocol

from .social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
    default_provider,
)
from .social_history import SocialContentHistory, SocialContentReceipt

FetchFailure = Literal["invalid", "temporary", "rate", "access"]
Job = tuple[SocialCategory, SocialProvider]


def providers_for(category: SocialCategory) -> tuple[SocialProvider, ...]:
    return ((SocialProvider.JOKEAPI, SocialProvider.QUOTATIONS)
            if category == SocialCategory.SINGLE else (default_provider(category),))


@dataclass(frozen=True, slots=True)
class SocialFetchResult:
    token: object
    category: SocialCategory
    content: PreparedSocialContent | None = None
    failure: FetchFailure | None = None
    retry_at: float | None = None


class SocialContentWorker(Protocol):
    def start(self, category: SocialCategory, token: object,
              provider: SocialProvider | None = None) -> None: ...

    def poll(self) -> SocialFetchResult | None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class SocialSelection:
    status: Literal["ready", "waiting", "error", "disabled", "limited"]
    content: PreparedSocialContent | None = None


class SocialContentCoordinator:
    """Readiness changes no pet needs; all providers share the existing worker."""

    def __init__(
        self, worker: SocialContentWorker, *,
        history: SocialContentHistory = SocialContentHistory(),
        wall_time: Callable[[], float] | None = None,
        persist_requests: Callable[[], OSError | None] = lambda: None,
    ) -> None:
        self._worker, self._wall_time = worker, wall_time or time.time
        self._persist_requests = persist_requests
        self._buffers: dict[SocialCategory, deque[PreparedSocialContent]] = {
            category: deque() for category in SocialCategory
        }
        self._enabled = False
        self._closed = False
        self._generation = 0
        self._request: tuple[object, Job, int] | None = None
        self._waiting: SocialCategory | None = None
        self._offered: PreparedSocialContent | None = None
        self._failed: set[Job] = set()
        self._attempts: dict[Job, int] = {}
        self._history = replace(
            history, requests=history.requests.pruned(self._wall_time()),
        )
        self._storage_failed = False

    @property
    def history(self) -> SocialContentHistory:
        return self._history

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
        # Opt-out never resets persisted quotas, blocks or failed refill cycles.
        for buffer in self._buffers.values():
            buffer.clear()
        self._pump()

    def select(self, category: SocialCategory) -> SocialSelection:
        if not isinstance(category, SocialCategory):
            raise ValueError("Unknown social category")
        self.cancel_selection()
        if not self.enabled:
            return SocialSelection("disabled")
        self._storage_failed = False
        for provider in providers_for(category):
            job = category, provider
            if job in self._failed:
                self._failed.discard(job)
                self._attempts[job] = 0
        buffer = self._buffers[category]
        if buffer:
            # Alternate admitted sources when both are ready; never fetch just
            # to enforce a ratio or delay available content for the other source.
            last = next((e.identity.split(":", 1)[0]
                         for e in reversed(self.history.entries)
                         if e.category == category), "")
            preferred = (SocialProvider.QUOTATIONS if last == "jokeapi"
                         else SocialProvider.JOKEAPI)
            item = next((e for e in buffer if e.provider == preferred), buffer[0])
            buffer.remove(item)
            self._offered = item
            self._pump()
            return SocialSelection("ready", item)
        self._waiting = category
        self._pump()
        status = self._unavailable()
        if status:
            self._waiting = None
            return SocialSelection(status)
        return SocialSelection("waiting")

    def cancel_selection(self) -> None:
        self._waiting = None
        self._offered = None

    def accept(self, content: PreparedSocialContent) -> None:
        if self._offered is not content:
            raise ValueError("Conversation is no longer offered")
        self._offered = None
        self._history = self._history.admitted(SocialContentReceipt(
            content.category, content.identity, content.fingerprint,
        ))

    def _duplicate(self, item: PreparedSocialContent) -> bool:
        known = (*self._history.entries,
                 *((self._offered,) if self._offered else ()),
                 *(entry for buffer in self._buffers.values() for entry in buffer))
        return any(entry.identity == item.identity
                   or entry.fingerprint == item.fingerprint for entry in known)

    def _persist(self) -> bool:
        try:
            self._storage_failed = self._persist_requests() is not None
        except OSError:
            self._storage_failed = True
        return not self._storage_failed

    def poll(self) -> SocialSelection | None:
        if self._closed:
            return None
        result = self._worker.poll()
        update: SocialSelection | None = None
        if result is not None and self._request is not None:
            token, job, generation = self._request
            category, provider = job
            if result.token is token:
                self._request = None
                # Even stale/disabled replies can carry a provider-wide quota.
                if result.retry_at is not None:
                    self._history = replace(self.history, requests=(
                        self.history.requests.blocked(provider, result.retry_at)))
                    self._persist()
                if self.enabled and generation == self._generation:
                    item = result.content
                    valid = (item is not None and result.failure is None
                             and result.category == category
                             and item.category == category and item.provider == provider
                             and not self._duplicate(item))
                    if valid:
                        assert item is not None
                        self._attempts[job] = 0
                        if self._waiting == category:
                            self._waiting = None
                            self._offered = item
                            update = SocialSelection("ready", item)
                        else:
                            self._buffers[category].append(item)
                    elif result.failure not in (None, "invalid"):
                        self._failed.add(job)
                    elif self._attempts.get(job, 0) >= 3:
                        self._failed.add(job)
                        self._history = replace(self.history, requests=(
                            self.history.requests.blocked(
                                provider, self._wall_time() + 600)))
                        self._persist()
        self._pump()
        status = self._unavailable()
        if self._waiting is not None and status:
            self._waiting = None
            update = SocialSelection(status)
        return update

    def _unavailable(self) -> Literal["error", "limited"] | None:
        if self._waiting is None:
            return None
        if self._storage_failed:
            return "error"
        if self._request is not None and self._request[1][0] == self._waiting:
            return None
        jobs = [(self._waiting, p) for p in providers_for(self._waiting)
                if (self._waiting, p) not in self._failed]
        if not jobs:
            return "error"
        now = self._wall_time()
        if all(self.history.requests.ready_at(p, now) > now + 30 for _, p in jobs):
            return "limited"
        return None

    def _pump(self) -> None:
        if not self.enabled or self._request is not None or self._storage_failed:
            return
        now = self._wall_time()
        candidates = [(category, provider) for category in SocialCategory
                      if self.count(category) < 2
                      for provider in providers_for(category)
                      if (category, provider) not in self._failed
                      and self.history.requests.ready_at(provider, now) <= now]
        if not candidates:
            return
        category, provider = min(candidates, key=lambda job: (
            job[0] != self._waiting, self.count(job[0]),
            sum(e.provider == job[1] for e in self._buffers[job[0]]),
        ))
        job = category, provider
        self._history = replace(self.history, requests=(
            self.history.requests.reserved(provider, now)))
        # Save reservation before network dispatch. A failed write forbids HTTP.
        if not self._persist():
            return
        self._attempts[job] = self._attempts.get(job, 0) + 1
        token = object()
        self._request = (token, job, self._generation)
        self._worker.start(category, token, provider)

    def close(self) -> None:
        if self._closed:
            return
        self.set_enabled(False)
        self._closed = True
        self._worker.close()
