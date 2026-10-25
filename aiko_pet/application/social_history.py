"""Bounded admitted-content receipts, separate from pet experiences and buffers."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .horoscope_models import HoroscopeDay
from .social_content import SocialCategory
from .social_requests import SocialRequestHistory

RECENT_CONTENTS_PER_CATEGORY = 100


@dataclass(frozen=True, slots=True)
class SocialContentReceipt:
    category: SocialCategory
    identity: str
    fingerprint: str
    intro_variant: int | None = None


@dataclass(frozen=True, slots=True)
class SocialContentHistory:
    """Per-category receipts plus one bounded, resumable daily horoscope."""

    entries: tuple[SocialContentReceipt, ...] = ()
    requests: SocialRequestHistory = SocialRequestHistory()
    horoscope: HoroscopeDay | None = None

    def admitted(self, receipt: SocialContentReceipt) -> SocialContentHistory:
        others = tuple(e for e in self.entries if e.category != receipt.category)
        recent = tuple(e for e in self.entries if e.category == receipt.category)
        return replace(self, entries=(
            *others, *recent[-(RECENT_CONTENTS_PER_CATEGORY - 1):], receipt,
        ))
