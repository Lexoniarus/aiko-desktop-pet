"""Finite provider budgets and expiring wall-clock receipts, without pet time."""

from __future__ import annotations

from dataclasses import dataclass

from .social_content import SocialProvider

# Client caps, deliberately below JokeAPI's published 120 requests/minute.
# Unknown public quotas are not treated as unlimited.
REQUEST_CAPS: dict[SocialProvider, tuple[int, int, int]] = {
    SocialProvider.JOKEAPI: (5, 60, 300),
    SocialProvider.QUOTATIONS: (10, 20, 60),
    SocialProvider.FACTS: (10, 20, 60),
}
MAX_REQUEST_RECEIPTS = sum(cap[2] for cap in REQUEST_CAPS.values())


@dataclass(frozen=True, slots=True)
class SocialRequestReceipt:
    provider: SocialProvider
    at: float


@dataclass(frozen=True, slots=True)
class SocialProviderBlock:
    provider: SocialProvider
    until: float


@dataclass(frozen=True, slots=True)
class SocialRequestHistory:
    attempts: tuple[SocialRequestReceipt, ...] = ()
    blocks: tuple[SocialProviderBlock, ...] = ()

    def pruned(self, now: float) -> SocialRequestHistory:
        return SocialRequestHistory(
            tuple(e for e in self.attempts if e.at > now - 86400),
            tuple(e for e in self.blocks if e.until > now),
        )

    def ready_at(self, provider: SocialProvider, now: float) -> float:
        interval, hourly, daily = REQUEST_CAPS[provider]
        stamps = sorted(e.at for e in self.attempts if e.provider == provider
                        and e.at > now - 86400)
        ready = max((b.until for b in self.blocks if b.provider == provider),
                    default=now)
        if stamps:
            ready = max(ready, stamps[-1] + interval)
        if len(stamps) >= daily:
            ready = max(ready, stamps[-daily] + 86400)
        hours = [stamp for stamp in stamps if stamp > now - 3600]
        if len(hours) >= hourly:
            ready = max(ready, hours[-hourly] + 3600)
        return ready

    def reserved(self, provider: SocialProvider, now: float) -> SocialRequestHistory:
        if self.ready_at(provider, now) > now:
            raise ValueError("Provider request budget exhausted")
        current = self.pruned(now)
        return SocialRequestHistory(
            (*current.attempts, SocialRequestReceipt(provider, now)), current.blocks,
        )

    def blocked(self, provider: SocialProvider, until: float) -> SocialRequestHistory:
        until = max((until, *(b.until for b in self.blocks if b.provider == provider)))
        return SocialRequestHistory(
            self.attempts,
            (
                *(b for b in self.blocks if b.provider != provider),
                SocialProviderBlock(provider, until),
            ),
        )
