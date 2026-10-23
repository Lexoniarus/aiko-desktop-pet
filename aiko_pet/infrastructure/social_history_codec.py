"""Versioned receipt-only social history in the existing local save."""

from typing import Any

from ..application.social_content import SocialCategory
from ..application.social_history import (
    RECENT_CONTENTS_PER_CATEGORY,
    SocialContentHistory,
    SocialContentReceipt,
)
from ..pet.catalog_validation import enum_value, object_fields
from .social_request_codec import decode_social_requests, encode_social_requests


def decode_social_history(raw: Any) -> SocialContentHistory:
    if not isinstance(raw, dict) or type(raw.get("version")) is not int:
        raise ValueError("Unsupported social history version")
    version = raw["version"]
    if version not in (1, 2):
        raise ValueError("Unsupported social history version")
    row = object_fields(raw, ("version", "entries", "requests") if version == 2
                        else ("version", "entries"), context="social history")
    entries = row["entries"]
    if (not isinstance(entries, list)
            or len(entries) > len(SocialCategory) * RECENT_CONTENTS_PER_CATEGORY):
        raise ValueError("Unbounded social history")
    result = []
    counts = dict.fromkeys(SocialCategory, 0)
    identities: set[str] = set()
    fingerprints: set[str] = set()
    for entry in entries:
        item = object_fields(entry, ("category", "identity", "fingerprint"),
                             context="social receipt")
        category = enum_value(
            item["category"], SocialCategory, context="social category",
        )
        identity, fingerprint = item["identity"], item["fingerprint"]
        prefix = ("uselessfacts:" if category == SocialCategory.FACT else
                  "zitat-service:" if category == SocialCategory.SINGLE
                  and isinstance(identity, str)
                  and identity.startswith("zitat-service:")
                  else "jokeapi:")
        if (not isinstance(identity, str) or not identity.startswith(prefix)
                or not 1 <= len(identity.removeprefix(prefix)) <= 128
                or any(char.isspace() or ord(char) < 32 for char in identity)
                or category != SocialCategory.FACT
                and not all("0" <= char <= "9" for char in identity[len(prefix):])):
            raise ValueError("Invalid social provider identity")
        if (not isinstance(fingerprint, str) or len(fingerprint) != 64
                or any(char not in "0123456789abcdef" for char in fingerprint)):
            raise ValueError("Invalid social content fingerprint")
        counts[category] += 1
        if (counts[category] > RECENT_CONTENTS_PER_CATEGORY
                or identity in identities or fingerprint in fingerprints):
            raise ValueError("Duplicate or excessive social history")
        identities.add(identity)
        fingerprints.add(fingerprint)
        result.append(SocialContentReceipt(category, identity, fingerprint))
    if version == 2:
        return SocialContentHistory(
            tuple(result), decode_social_requests(row["requests"]),
        )
    return SocialContentHistory(tuple(result))


def encode_social_history(history: SocialContentHistory) -> dict[str, Any]:
    return dict(version=2, entries=[
        dict(category=e.category.value, identity=e.identity, fingerprint=e.fingerprint)
        for e in history.entries
    ], requests=encode_social_requests(history.requests))


def valid_social_history(raw: Any) -> bool:
    try:
        decode_social_history(raw)
    except (ValueError, TypeError, OverflowError):
        return False
    return True
