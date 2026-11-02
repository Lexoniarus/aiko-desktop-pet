"""Bounded admitted-content receipts, separate from pet experiences and buffers."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .social_candidates import MAX_JOKE_EXCLUSIONS, JokeExclusion
from .social_content import SocialCategory
from .social_requests import SocialRequestHistory

RECENT_CONTENTS_PER_CATEGORY = 100
JOKE_REPEAT_WINDOW = 10


@dataclass(frozen=True, slots=True)
class SocialContentReceipt:
    category: SocialCategory
    identity: str
    fingerprint: str
    intro_variant: int | None = None


@dataclass(frozen=True, slots=True)
class SocialContentHistory:
    """Per-category online content receipts and request limits."""

    entries: tuple[SocialContentReceipt, ...] = ()
    requests: SocialRequestHistory = SocialRequestHistory()
    exclusions: tuple[JokeExclusion, ...] = ()

    @property
    def protected_entries(self) -> tuple[SocialContentReceipt, ...]:
        """Keep the bounded archive, but release old jokes within a finite pool."""
        return tuple(
            entry
            for category in (SocialCategory.SINGLE, SocialCategory.TWO_PARTS,
                             SocialCategory.FACT)
            for entry in tuple(e for e in self.entries if e.category == category)[
                -(RECENT_CONTENTS_PER_CATEGORY if category == SocialCategory.FACT
                  else JOKE_REPEAT_WINDOW):
            ]
        )

    def excluded(self, entry: JokeExclusion, now: float) -> SocialContentHistory:
        retained = tuple(e for e in self.exclusions if e.until > now
                         and (e.category, e.lower, e.upper)
                         != (entry.category, entry.lower, entry.upper))
        return replace(self, exclusions=(*retained[-(MAX_JOKE_EXCLUSIONS - 1):], entry))

    def admitted(self, receipt: SocialContentReceipt) -> SocialContentHistory:
        retained = tuple(e for e in self.entries if e.identity != receipt.identity
                         and e.fingerprint != receipt.fingerprint)
        others = tuple(e for e in retained if e.category != receipt.category)
        recent = tuple(e for e in retained if e.category == receipt.category)
        return replace(
            self,
            entries=(
                *others,
                *recent[-(RECENT_CONTENTS_PER_CATEGORY - 1) :],
                receipt,
            ),
        )
