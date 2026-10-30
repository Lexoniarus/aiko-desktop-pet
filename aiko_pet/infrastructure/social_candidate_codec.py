"""Strict, bounded candidate exclusions; no provider bodies are saved here."""

import math
from typing import Any, cast

from ..application.social_candidates import (
    MAX_JOKE_EXCLUSIONS,
    MAX_JOKE_ID,
    JokeExclusion,
    RejectionReason,
)
from ..pet.catalog_validation import object_fields
from ..pet.social_content_evidence import SocialCategory


def decode_joke_exclusions(raw: Any) -> tuple[JokeExclusion, ...]:
    if not isinstance(raw, list) or len(raw) > MAX_JOKE_EXCLUSIONS:
        raise ValueError("Unbounded joke exclusions")
    result = []
    seen = set()
    for value in raw:
        row = object_fields(
            value, ("category", "lower", "upper", "reason", "until", "revision"),
            context="joke exclusion",
        )
        lower, upper, until = row["lower"], row["upper"], row["until"]
        if (row["category"] not in ("single", "twopart")
                or type(lower) is not int or type(upper) is not int
                or not 0 <= lower <= upper <= MAX_JOKE_ID
                or row["reason"] not in
                ("format", "incomplete", "length", "no_match", "duplicate")
                or type(until) not in (int, float) or not math.isfinite(until)
                or not 0 <= until <= 253402300799
                or type(row["revision"]) is not int or row["revision"] < 1):
            raise ValueError("Invalid joke exclusion")
        key = row["category"], lower, upper
        if key in seen:
            raise ValueError("Duplicate joke exclusion")
        seen.add(key)
        result.append(JokeExclusion(
            SocialCategory(row["category"]), lower, upper,
            cast(RejectionReason, row["reason"]), float(until), row["revision"],
        ))
    return tuple(result)


def encode_joke_exclusions(entries: tuple[JokeExclusion, ...]) -> list[dict[str, Any]]:
    return [dict(category=e.category.value, lower=e.lower, upper=e.upper,
                 reason=e.reason, until=e.until, revision=e.revision) for e in entries]
