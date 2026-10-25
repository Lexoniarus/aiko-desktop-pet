"""Prepare source-aware German API content for the existing reaction player."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, replace
from typing import Any
from urllib.parse import urlsplit

from ..pet.balance import BALANCE
from ..pet.content import GERMAN_TEXT
from ..pet.mind.catalog import Reaction
from ..pet.mind.reaction_sequence import Cue
from ..pet.social_content_evidence import SocialCategory as SocialCategory
from ..pet.social_content_evidence import SocialContentEvidence
from ..pet.social_content_evidence import SocialProvider as SocialProvider
from .horoscope_models import HoroscopeText

BUFFERED_CATEGORIES = (
    SocialCategory.SINGLE, SocialCategory.TWO_PARTS, SocialCategory.FACT,
)
SOCIAL_INTRO_VARIANTS = 3


def default_provider(category: SocialCategory) -> SocialProvider:
    if category == SocialCategory.HOROSCOPE:
        return SocialProvider.ASTROWAY
    return (SocialProvider.FACTS if category == SocialCategory.FACT
            else SocialProvider.JOKEAPI)


@dataclass(frozen=True, slots=True)
class PreparedSocialContent:
    category: SocialCategory
    identity: str
    fingerprint: str
    source: str
    source_url: str
    permalink: str
    reaction: Reaction
    provider: SocialProvider
    author: str = ""
    author_url: str = ""
    license_name: str = ""
    license_url: str = ""
    horoscope: HoroscopeText | None = None
    intro_variant: int | None = None
    evidence: SocialContentEvidence | None = None


def _intro_cue(category: SocialCategory, variant: int) -> Cue:
    key = f"social.intro.{category.value}" + (f"_alt{variant}" if variant else "")
    return Cue.text(GERMAN_TEXT.format(key))


def with_intro_variant(
    content: PreparedSocialContent, variant: int,
) -> PreparedSocialContent:
    """Replace framing only; provider text, identity and fingerprint stay intact."""
    if (content.category not in BUFFERED_CATEGORIES or type(variant) is not int
            or not 0 <= variant < SOCIAL_INTRO_VARIANTS):
        raise ValueError("Invalid social introduction variant")
    return replace(
        content, intro_variant=variant,
        reaction=replace(content.reaction, beats=(
            _intro_cue(content.category, variant), *content.reaction.beats[1:],
        )),
    )


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


def _short_content(value: object, *, joke: bool) -> str:
    """Inspect structure before whitespace normalization can conceal a story."""
    text = _text(value)
    assert isinstance(value, str)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    dialogue = re.findall(r'\b[\w-]+:(?:\s+|(?=["„»]))', value)
    stages = re.findall(r"\b(?:Frage|Antwort|Pointe|Setup|Delivery)\s*:",
                        value, re.IGNORECASE)
    if (len(text) > 125 or re.search(r"\n\s*\n", value)
            or len(dialogue) >= 2 or len(stages) >= 2):
        raise ValueError("Saying must be one complete short content bubble")
    if joke and ("\n" in value.strip() or "\r" in value.strip()):
        raise ValueError("Multi-line joke setup/dialogue is not a one-liner")
    return text


def _quotation(payload: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    if payload.get("language") != "de":
        raise ValueError("Quotation is not German")
    text = _short_content(payload.get("quote"), joke=False)
    link = _url(payload.get("link"))
    match = re.fullmatch(r"https://www\.zitat-service\.de/de/quotations/([0-9]+)", link)
    if match is None or len(match[1]) > 128:
        raise ValueError("Invalid quotation identity")
    author = _text(payload.get("authorName"))
    if len(GERMAN_TEXT.format("social.quote_author", author=author)) > 125:
        raise ValueError("Author attribution exceeds one bubble")
    author_url = _url(payload["authorLink"]) if payload.get("authorLink") else ""
    source = _text(payload["source"]) if payload.get("source") else "Zitat-Service"
    if len(source) > 1000:
        raise ValueError("Oversized quotation source")
    source_url = _url(payload["sourceLink"]) if payload.get("sourceLink") else ""
    return text, match[1], author, author_url, source, source_url


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
    *, provider: SocialProvider | None = None,
) -> PreparedSocialContent:
    """Validate provider fields before a buffer slot can become ready."""
    if not isinstance(category, SocialCategory) or not isinstance(payload, dict):
        raise ValueError("Invalid social content")
    if category == SocialCategory.HOROSCOPE:
        raise ValueError("Horoscope requires its dated validator")
    provider = provider or default_provider(category)
    author, author_url, license_name, license_url = "", "", "", ""
    parts: tuple[str, ...]
    if provider == SocialProvider.QUOTATIONS:
        if category != SocialCategory.SINGLE:
            raise ValueError("Quotations belong to Sprüche only")
        text, identifier_text, author, author_url, source, source_url = _quotation(
            payload,
        )
        identity = f"zitat-service:{identifier_text}"
        permalink = payload["link"]
        parts = (text,)
        license_name = "CC BY 4.0"
        license_url = "https://creativecommons.org/licenses/by/4.0/"
    elif provider != default_provider(category):
        raise ValueError("Provider/category mismatch")
    elif category == SocialCategory.FACT:
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
        parts = ((_short_content(payload.get("joke"), joke=True),)
                 if category == SocialCategory.SINGLE else (
                     _text(payload.get("setup")), _text(payload.get("delivery")),
                 ))
    fingerprint = hashlib.sha256(" ".join(parts).casefold().encode()).hexdigest()
    # Initial framing is deterministic. The coordinator rotates it against the
    # last admitted receipt when offering it, before the immutable playback.
    variant = int(fingerprint[:2], 16) % SOCIAL_INTRO_VARIANTS
    beats = [_intro_cue(category, variant)]
    for index, part in enumerate(parts):
        if index:
            beats.append(Cue(
                "pause", "",
                BALANCE.integer("dialogue", "conversation_punchline_pause_ms"),
            ))
        beats.extend(_segments(part))
    if author:
        beats.append(Cue.text(GERMAN_TEXT.format("social.quote_author", author=author)))
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
        provider, author, author_url, license_name, license_url,
        intro_variant=variant,
        evidence=SocialContentEvidence(
            category, provider, identity, fingerprint, parts,
            source, source_url, permalink, author, author_url,
            license_name, license_url,
        ),
    )
