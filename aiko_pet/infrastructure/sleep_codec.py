"""Strict optional sleep episode values inside the compatible outer v1 save."""

from __future__ import annotations

import math
from dataclasses import asdict
from typing import Any

from ..pet.sleep import SleepEpisode, setting


def encode_sleep(episode: SleepEpisode) -> dict[str, Any]:
    result = {"version": 1, **asdict(episode)}
    result["failed_food_sources"] = list(episode.failed_food_sources)
    return result


def decode_sleep(raw: Any, elapsed: float) -> SleepEpisode:
    if (
        not isinstance(raw, dict)
        or type(raw.get("version")) is not int
        or raw["version"] != 1
    ):
        raise ValueError("Unsupported sleep episode")
    names = (
        "kind",
        "started",
        "slept_seconds",
        "wake_wall",
        "protect_until",
        "care_break",
        "search_until",
        "intake_until",
        "food_failed",
        "failed_food_sources",
    )
    if set(raw) != {"version", *names}:
        raise ValueError("Invalid sleep fields")
    if raw["kind"] not in ("", "main", "nap", "recovery"):
        raise ValueError("Invalid sleep kind")
    for name in ("care_break", "food_failed"):
        if type(raw[name]) is not bool:
            raise ValueError("Invalid sleep flag")
    for name in (
        "started",
        "slept_seconds",
        "wake_wall",
        "protect_until",
        "search_until",
        "intake_until",
    ):
        value = raw[name]
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError("Invalid sleep time")
    if (
        raw["started"] > elapsed
        or raw["slept_seconds"] > elapsed - raw["started"] + 0.01
        or raw["protect_until"] > elapsed + setting("manual_protection_seconds") + .01
        or raw["search_until"] > elapsed + setting("search_seconds") + .01
        or raw["intake_until"] > elapsed + setting("portion_seconds") + .01
        or raw["wake_wall"] > 4_000_000_000
        or (not raw["kind"] and (raw["care_break"] or raw["food_failed"]))
    ):
        raise ValueError("Inconsistent sleep timeline")
    sources = raw["failed_food_sources"]
    if (
        not isinstance(sources, list)
        or len(sources) > 4096
        or any(not isinstance(v, str) or not 1 <= len(v) <= 128 for v in sources)
        or len(set(sources)) != len(sources)
    ):
        raise ValueError("Invalid failed food sources")
    return SleepEpisode(
        kind=raw["kind"],
        started=float(raw["started"]),
        slept_seconds=float(raw["slept_seconds"]),
        wake_wall=float(raw["wake_wall"]),
        protect_until=float(raw["protect_until"]),
        care_break=raw["care_break"],
        search_until=float(raw["search_until"]),
        intake_until=float(raw["intake_until"]),
        food_failed=raw["food_failed"],
        failed_food_sources=tuple(sources),
    )


def valid_sleep(raw: Any, elapsed: float) -> bool:
    try:
        decode_sleep(raw, elapsed)
    except (ValueError, TypeError, KeyError, OverflowError):
        return False
    return True
