"""One owner-thread scheduler, mixed Sprueche stock and persistent request caps."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, replace
from random import choice
from typing import Callable, Literal

from .social_candidates import (
    JOKE_EXCLUSION_SECONDS,
    IdRange,
    JokeCatalog,
    JokeExclusion,
)
from .social_content import (
    BUFFERED_CATEGORIES,
    SOCIAL_INTRO_VARIANTS,
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
    default_provider,
    with_intro_variant,
)
from .social_fetch import SocialContentWorker, SocialFetchRequest
from .social_history import SocialContentHistory, SocialContentReceipt
from .social_repeat import JokeRepeatPlan, SocialRepeatPolicy
from .storage_contracts import StorageError

Job = tuple[SocialCategory, SocialProvider]


def providers_for(category: SocialCategory) -> tuple[SocialProvider, ...]:
    return (
        (SocialProvider.JOKEAPI, SocialProvider.QUOTATIONS, SocialProvider.WITZAPI)
        if category == SocialCategory.SINGLE
        else (SocialProvider.JOKEAPI, SocialProvider.WITZAPI)
        if category == SocialCategory.TWO_PARTS
        else (default_provider(category),)
    )


@dataclass(frozen=True, slots=True)
class SocialSelection:
    status: Literal[
        "ready", "waiting", "error", "disabled", "limited", "sign", "completed",
        "exhausted", "search_paused",
    ]
    content: PreparedSocialContent | None = None


@dataclass(frozen=True, slots=True)
class _PendingFetch:
    token: object
    job: Job
    generation: int
    request: SocialFetchRequest
    released_identity: str | None = None


class SocialContentCoordinator:
    """Readiness changes no pet needs; all providers share the existing worker."""

    def __init__(
        self,
        worker: SocialContentWorker,
        *,
        history: SocialContentHistory = SocialContentHistory(),
        wall_time: Callable[[], float] | None = None,
        persist_requests: Callable[[], StorageError | None] = lambda: None,
        joke_catalog: JokeCatalog | None = None,
        local_content: tuple[PreparedSocialContent, ...] = (),
    ) -> None:
        self._worker, self._wall_time = worker, wall_time or time.time
        self._persist_requests = persist_requests
        self._buffers: dict[SocialCategory, deque[PreparedSocialContent]] = {
            category: deque() for category in BUFFERED_CATEGORIES
        }
        self._enabled = False
        self._closed = False
        self._generation = 0
        self._request: _PendingFetch | None = None
        self._catalog = joke_catalog
        self._catalog_failed = False
        self._content_failed: set[Job] = set()
        self._waiting: SocialCategory | None = None
        self._offered: PreparedSocialContent | None = None
        self._failed: set[Job] = set()
        self._attempts: dict[Job, int] = {}
        self._history = replace(
            history,
            requests=history.requests.pruned(self._wall_time()),
        )
        self._storage_failed = False
        self._local_content = local_content

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
        return len(self._buffers.get(category, ()))

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
        retrying = self._waiting != category
        self.cancel_selection()
        if not self.enabled:
            return SocialSelection("disabled")
        self._storage_failed = False
        if category not in BUFFERED_CATEGORIES:
            raise ValueError("Local books are not social API content")
        for provider in providers_for(category):
            if retrying and provider == SocialProvider.JOKEAPI:
                self._catalog_failed = False
            job = category, provider
            if retrying and job in self._failed:
                self._failed.discard(job)
                self._attempts[job] = 0
                self._content_failed.discard(job)
        buffer = self._buffers[category]
        if buffer:
            # Alternate admitted sources when both are ready; never fetch just
            # to enforce a ratio or delay available content for the other source.
            last = next(
                (
                    e.identity.split(":", 1)[0]
                    for e in reversed(self.history.entries)
                    if e.category == category
                ),
                "",
            )
            preferred = (
                SocialProvider.QUOTATIONS
                if last == "jokeapi"
                else SocialProvider.JOKEAPI
            )
            item = next((e for e in buffer if e.provider == preferred), buffer[0])
            buffer.remove(item)
            item = self._offer(item)
            self._pump()
            return SocialSelection("ready", item)
        local = self.local_candidates(category)
        if local:
            item = self._offer(choice(local))
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

    def _offer(self, item: PreparedSocialContent) -> PreparedSocialContent:
        """Rotate from admitted history; warming/cancellation never advance it."""
        last = next(
            (
                entry
                for entry in reversed(self.history.entries)
                if entry.category == item.category
            ),
            None,
        )
        if last is not None:
            previous = (
                last.intro_variant
                if last.intro_variant is not None
                else int(last.fingerprint[:2], 16) % SOCIAL_INTRO_VARIANTS
            )
            item = with_intro_variant(item, (previous + 1) % SOCIAL_INTRO_VARIANTS)
        self._offered = item
        return item

    def accept(self, content: PreparedSocialContent) -> None:
        if self._offered is not content:
            raise ValueError("Conversation is no longer offered")
        self._offered = None
        self._history = self._history.admitted(
            SocialContentReceipt(
                content.category,
                content.identity,
                content.fingerprint,
                content.intro_variant,
            )
        )

    def _repeat_policy(self) -> SocialRepeatPolicy:
        occupied = tuple(e for buffer in self._buffers.values() for e in buffer)
        if self._offered is not None:
            occupied += (self._offered,)
        return SocialRepeatPolicy(self.history.entries, occupied)

    def _duplicate(
        self, item: PreparedSocialContent, *, released_identity: str | None = None,
    ) -> bool:
        return not self._repeat_policy().permits(
            item, released_identity=released_identity,
        )

    def local_candidates(
        self, category: SocialCategory,
    ) -> tuple[PreparedSocialContent, ...]:
        pool = tuple(e for e in self._local_content if e.category == category)
        if not pool:
            return ()
        policy = self._repeat_policy()
        return tuple(e for e in pool if policy.permits(e, local_pool_size=len(pool)))

    def _ranges(self, category: SocialCategory) -> tuple[IdRange, ...] | None:
        return self._joke_plan(category).ranges

    def _joke_plan(self, category: SocialCategory) -> JokeRepeatPlan:
        if self._catalog is None or self._catalog.valid_until <= self._wall_time():
            return JokeRepeatPlan(None)
        return self._repeat_policy().joke_candidates(
            self._catalog, category, self.history.exclusions,
            self._wall_time(),
        )

    def _exhausted(self, job: Job) -> bool:
        return job[1] == SocialProvider.JOKEAPI and self._ranges(job[0]) == ()

    def _persist(self) -> bool:
        try:
            self._storage_failed = self._persist_requests() is not None
        except StorageError:
            self._storage_failed = True
        return not self._storage_failed

    def poll(self) -> SocialSelection | None:
        if self._closed:
            return None
        result = self._worker.poll()
        update: SocialSelection | None = None
        if result is not None and self._request is not None:
            pending = self._request
            token, job = pending.token, pending.job
            generation, request = pending.generation, pending.request
            category, provider = job
            if result.token is token:
                self._request = None
                # Even stale/disabled replies can carry a provider-wide quota.
                if result.retry_at is not None:
                    self._history = replace(
                        self.history,
                        requests=(
                            self.history.requests.blocked(provider, result.retry_at)
                        ),
                    )
                    self._persist()
                if self.enabled and generation == self._generation:
                    item = result.content
                    duplicate = item is not None and self._duplicate(
                        item, released_identity=pending.released_identity,
                    )
                    if request.metadata:
                        if result.catalog is not None and result.failure is None:
                            self._catalog = result.catalog
                        else:
                            self._catalog_failed = True
                    elif provider == SocialProvider.JOKEAPI:
                        rejected_range = None
                        reason = result.reason
                        if result.failure == "empty":
                            rejected_range = request.id_range
                        elif (result.failure == "rejected"
                              and result.rejected_id is not None):
                            rejected_range = (result.rejected_id, result.rejected_id)
                        elif item is not None and duplicate:
                            identifier = item.identity.removeprefix("jokeapi:")
                            if identifier.isascii() and identifier.isdigit():
                                rejected_range = (int(identifier), int(identifier))
                                reason = "duplicate"
                        if rejected_range is not None and reason is not None:
                            self._history = self.history.excluded(
                                JokeExclusion(
                                    category, *rejected_range, reason,
                                    self._wall_time() + JOKE_EXCLUSION_SECONDS,
                                ), self._wall_time(),
                            )
                            self._persist()
                    valid = (
                        item is not None
                        and result.failure is None
                        and result.category == category
                        and item.category == category
                        and item.provider == provider
                        and not duplicate
                    )
                    if request.metadata:
                        pass
                    elif valid:
                        assert item is not None
                        self._attempts[job] = 0
                        if self._waiting == category:
                            self._waiting = None
                            item = self._offer(item)
                            update = SocialSelection("ready", item)
                        else:
                            self._buffers[category].append(item)
                    elif result.failure not in (None, "invalid", "rejected", "empty"):
                        self._failed.add(job)
                    elif self._attempts.get(job, 0) >= 3:
                        self._failed.add(job)
                        self._content_failed.add(job)
        self._pump()
        status = self._unavailable()
        if self._waiting is not None and status:
            self._waiting = None
            update = SocialSelection(status)
        return update

    def _unavailable(
        self,
    ) -> Literal["error", "limited", "exhausted", "search_paused"] | None:
        if self._waiting is None:
            return None
        if self._storage_failed:
            return "error"
        if self._request is not None and self._request.job[0] == self._waiting:
            return None
        all_jobs = [(self._waiting, p) for p in providers_for(self._waiting)]
        if all(self._exhausted(job) for job in all_jobs):
            return "exhausted"
        jobs = [
            (self._waiting, p)
            for p in providers_for(self._waiting)
            if (self._waiting, p) not in self._failed
            and not self._exhausted((self._waiting, p))
            and not (p == SocialProvider.JOKEAPI and self._catalog_failed)
        ]
        if not jobs:
            return (
                "search_paused"
                if any(job in self._content_failed for job in all_jobs) else "error"
            )
        now = self._wall_time()
        if all(self.history.requests.ready_at(p, now) > now + 30 for _, p in jobs):
            return "limited"
        return None

    def _pump(self) -> None:
        if not self.enabled or self._request is not None or self._storage_failed:
            return
        now = self._wall_time()
        candidates = [
            (category, provider)
            for category in BUFFERED_CATEGORIES
            if self.count(category) < 2
            for provider in providers_for(category)
            if (category, provider) not in self._failed
            and not self._exhausted((category, provider))
            and not (provider == SocialProvider.JOKEAPI and self._catalog_failed)
            and self.history.requests.ready_at(provider, now) <= now
        ]
        if not candidates:
            return
        category, provider = min(
            candidates,
            key=lambda job: (
                job[0] != self._waiting,
                self.count(job[0]),
                sum(e.provider == job[1] for e in self._buffers[job[0]]),
            ),
        )
        job = category, provider
        plan = (self._joke_plan(category) if provider == SocialProvider.JOKEAPI
                else JokeRepeatPlan(None))
        ranges = plan.ranges
        request = SocialFetchRequest(
            metadata=provider == SocialProvider.JOKEAPI and ranges is None,
            id_range=choice(ranges) if ranges else None,
        )
        self._history = replace(
            self.history, requests=(self.history.requests.reserved(provider, now))
        )
        # Save reservation before network dispatch. A failed write forbids HTTP.
        if not self._persist():
            return
        if not request.metadata:
            self._attempts[job] = self._attempts.get(job, 0) + 1
        token = object()
        self._request = _PendingFetch(
            token, job, self._generation, request, plan.released_identity,
        )
        self._worker.start(category, token, provider, request=request)

    def close(self) -> None:
        if self._closed:
            return
        self.set_enabled(False)
        self._closed = True
        self._worker.close()
