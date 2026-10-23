"""Prepare source-aware German API content for the existing reaction player."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import urlsplit

from ..pet.balance import BALANCE
from ..pet.content import GERMAN_TEXT
from ..pet.mind.catalog import Reaction
from ..pet.mind.reaction_sequence import Cue


class SocialCategory(StrEnum):
    SINGLE = "single"
    TWO_PARTS = "twopart"
    FACT = "fact"


@dataclass(frozen=True, slots=True)
class PreparedSocialContent:
    category: SocialCategory
    identity: str
    fingerprint: str
    source: str
    source_url: str
    permalink: str
    reaction: Reaction


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 2500:
        raise ValueError("Missing or oversized social text")
    if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
        raise ValueError("Control character in social text")
    text = " ".join(value.split())
    if any(marker in text for marker in ("(...)", "(…)", "[...]", "[…]")):
        raise ValueError("Provider truncated the content")
    if text.endswith(("...", "…")):
        raise ValueError("Incomplete social text")
    return text


def _url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Invalid source URL")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Invalid source URL")
    return value


def _segments(text: str) -> tuple[Cue, ...]:
    """Keep every word, preferring sentence boundaries within the bubble limit."""
    remaining = text
    beats: list[Cue] = []
    while len(remaining) > 125:
        sentences = list(re.finditer(r"[.!?]\s+", remaining[:126]))
        end = sentences[-1].start() + 1 if sentences else remaining.rfind(" ", 0, 126)
        if end <= 0:
            raise ValueError("Social content contains an oversized word")
        beats.append(Cue.text(remaining[:end]))
        remaining = remaining[end:].lstrip()
    if remaining:
        beats.append(Cue.text(remaining))
    return tuple(beats)


def prepare_social_content(
    category: SocialCategory, payload: Any,
) -> PreparedSocialContent:
    """Validate provider fields before a buffer slot can become ready."""
    if not isinstance(category, SocialCategory) or not isinstance(payload, dict):
        raise ValueError("Invalid social content")
    parts: tuple[str, ...]
    if category == SocialCategory.FACT:
        if payload.get("language") != "de":
            raise ValueError("Fact is not German")
        identifier = payload.get("id")
        if (not isinstance(identifier, str) or not identifier or len(identifier) > 128
                or any(char.isspace() or ord(char) < 32 for char in identifier)):
            raise ValueError("Invalid fact identity")
        identity = f"uselessfacts:{identifier}"
        source = _text(payload.get("source"))
        if len(source) > 120:
            raise ValueError("Oversized source name")
        source_url = _url(payload.get("source_url"))
        permalink = _url(payload.get("permalink"))
        parts = (_text(payload.get("text")),)
    else:
        flags = payload.get("flags")
        if (payload.get("error") is not False or payload.get("safe") is not True
                or payload.get("lang") != "de" or payload.get("type") != category
                or not isinstance(flags, dict)
                or any(flags.get(flag) is not False for flag in (
                    "nsfw", "racist", "sexist", "religious", "political", "explicit",
                ))):
            raise ValueError("Joke language, type or safety flags rejected")
        identifier = payload.get("id")
        if type(identifier) is not int or identifier < 0 or len(str(identifier)) > 128:
            raise ValueError("Invalid joke identity")
        identity = f"jokeapi:{identifier}"
        source = "JokeAPI"
        source_url = "https://jokeapi.dev/"
        permalink = (
            f"https://v2.jokeapi.dev/joke/Any?lang=de&idRange={identifier}"
        )
        parts = ((_text(payload.get("joke")),)
                 if category == SocialCategory.SINGLE else (
                     _text(payload.get("setup")), _text(payload.get("delivery")),
                 ))
    fingerprint = hashlib.sha256(" ".join(parts).casefold().encode()).hexdigest()
    # Stable variation belongs to the prepared sequence, not mutable playback.
    # Only provider text participates in duplicate detection.
    variant = int(fingerprint[:2], 16) % 3
    intro_key = f"social.intro.{category.value}" + (f"_alt{variant}" if variant else "")
    beats = [Cue.text(GERMAN_TEXT.format(intro_key))]
    for index, part in enumerate(parts):
        if index:
            beats.append(Cue(
                "pause", "",
                BALANCE.integer("dialogue", "conversation_punchline_pause_ms"),
            ))
        beats.extend(_segments(part))
    if sum(beat.kind == "text" for beat in beats) > 5:
        raise ValueError("Social story exceeds five text bubbles")
    # React after the complete provider content, never before a punchline.
    # No extra text bubble displaces content from the existing five-text budget.
    if int(fingerprint[2:4], 16) % 3 == 0:
        emote = "idea" if category == SocialCategory.FACT else "faceHappy"
        beats.append(Cue("emote", emote, 900))
    return PreparedSocialContent(
        category, identity, fingerprint, source, source_url, permalink,
        Reaction(identity, tuple(beats), "idle", "talk", presentation="story"),
    )
