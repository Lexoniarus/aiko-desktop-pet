"""Bounded request metadata only; no credentials, provider text or permanent log."""

from __future__ import annotations

import math
from typing import Any

from ..application.social_content import SocialProvider
from ..application.social_requests import (
    MAX_REQUEST_RECEIPTS,
    REQUEST_CAPS,
    SocialProviderBlock,
    SocialRequestHistory,
    SocialRequestReceipt,
)
from ..pet.catalog_validation import enum_value, object_fields


def decode_social_requests(raw: Any) -> SocialRequestHistory:
    data = object_fields(raw, ("attempts", "blocks"), context="social requests")
    attempts, blocks = data["attempts"], data["blocks"]
    if (
        not isinstance(attempts, list)
        or len(attempts) > MAX_REQUEST_RECEIPTS + 60
        or not isinstance(blocks, list)
        or len(blocks) > len(SocialProvider) + 1
    ):
        raise ValueError("Unbounded social requests")

    def stamp(value: Any) -> float:
        if (type(value) not in (int, float) or not math.isfinite(value)
                or not 0 <= value <= 253402300799):
            raise ValueError("Invalid social request timestamp")
        return float(value)

    receipts = []
    counts = dict.fromkeys(SocialProvider, 0)
    for entry in attempts:
        row = object_fields(entry, ("provider", "at"), context="social request")
        if row["provider"] == "astroway":
            continue  # Retire the rejected provider from legacy saves.
        provider = enum_value(row["provider"], SocialProvider, context="provider")
        counts[provider] += 1
        if counts[provider] > REQUEST_CAPS[provider][2]:
            raise ValueError("Excessive provider request history")
        receipts.append(SocialRequestReceipt(provider, stamp(row["at"])))
    pauses = []
    seen = set()
    for entry in blocks:
        row = object_fields(entry, ("provider", "until"), context="provider block")
        if row["provider"] == "astroway":
            continue  # Retire the rejected provider from legacy saves.
        provider = enum_value(row["provider"], SocialProvider, context="provider")
        if provider in seen:
            raise ValueError("Duplicate provider block")
        seen.add(provider)
        pauses.append(SocialProviderBlock(provider, stamp(row["until"])))
    return SocialRequestHistory(tuple(receipts), tuple(pauses))


def encode_social_requests(history: SocialRequestHistory) -> dict[str, Any]:
    return {
        "attempts": [dict(provider=e.provider.value, at=e.at)
                     for e in history.attempts],
        "blocks": [dict(provider=e.provider.value, until=e.until)
                   for e in history.blocks],
    }
