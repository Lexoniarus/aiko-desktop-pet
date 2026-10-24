"""Bounded daily horoscope text and resumable calendar-day state, without I/O."""

from __future__ import annotations

import hashlib
from typing import Any

from ..pet.content import GERMAN_TEXT
from ..pet.mind.catalog import Reaction
from ..pet.mind.reaction_sequence import Cue
from .horoscope_models import ZODIAC_SIGNS, HoroscopeRequest, HoroscopeText, checked_day
from .social_content import (
    PreparedSocialContent,
    SocialCategory,
    SocialProvider,
    _segments,
    _text,
)


def prepare_horoscope_text(text: HoroscopeText) -> PreparedSocialContent:
    if text.sign not in ZODIAC_SIGNS:
        raise ValueError("Invalid zodiac sign")
    checked_day(text.date)
    parts = tuple(_text(v) for v in (text.disclaimer, text.overview, text.advice))
    footer = _text(text.footer)
    if len(footer) > 500 or "astroway" not in footer.casefold():
        raise ValueError("Missing or oversized provider attribution")
    beats = (
        Cue.text(GERMAN_TEXT.format("social.horoscope.enter")),
        *(cue for part in parts for cue in _segments(part)),
        Cue.text(GERMAN_TEXT.format("social.horoscope.exit")),
    )
    if len(beats) > 12:
        raise ValueError("Horoscope exceeds twelve complete text bubbles")
    identity = f"astroway:{text.date}:{text.sign}"
    fingerprint = hashlib.sha256(" ".join(parts).encode()).hexdigest()
    return PreparedSocialContent(
        SocialCategory.HOROSCOPE,
        identity,
        fingerprint,
        "AstroWay",
        "https://api.astroway.info/en/free/",
        "https://api.astroway.info/",
        Reaction(identity, beats, "idle", "talk", presentation="story"),
        SocialProvider.ASTROWAY,
        horoscope=text,
    )


def prepare_horoscope(payload: Any, request: HoroscopeRequest) -> PreparedSocialContent:
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        raise ValueError("Unsuccessful horoscope envelope")
    data = payload.get("data")
    if (
        not isinstance(data, dict)
        or data.get("sign") != request.sign
        or data.get("date") != request.date
        or data.get("period") != "daily"
        or data.get("language") != "de"
        or data.get("fallback")
        or payload.get("fallback")
    ):
        raise ValueError("Stale or mismatched horoscope")
    sections = data.get("sections")
    if not isinstance(sections, dict):
        raise ValueError("Missing horoscope sections")
    return prepare_horoscope_text(
        HoroscopeText(
            request.sign,
            request.date,
            _text(sections.get("overview")),
            _text(sections.get("advice")),
            _text(data.get("disclaimer")),
            _text(payload.get("_footer")),
        )
    )
