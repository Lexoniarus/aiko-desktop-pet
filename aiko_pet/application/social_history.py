"""Bounded admitted-content receipts, separate from pet experiences and buffers."""

from __future__ import annotations

from dataclasses import dataclass

from .social_content import SocialCategory

RECENT_CONTENTS_PER_CATEGORY = 10


@dataclass(frozen=True, slots=True)
class SocialContentReceipt:
    category: SocialCategory
    identity: str
    fingerprint: str


@dataclass(frozen=True, slots=True)
class SocialContentHistory:
    """Per-category ordered receipts; no provider words, URLs or playback."""

    entries: tuple[SocialContentReceipt, ...] = ()

    def admitted(self, receipt: SocialContentReceipt) -> SocialContentHistory:
        others = tuple(e for e in self.entries if e.category != receipt.category)
        recent = tuple(e for e in self.entries if e.category == receipt.category)
        return SocialContentHistory((
            *others, *recent[-(RECENT_CONTENTS_PER_CATEGORY - 1):], receipt,
        ))
