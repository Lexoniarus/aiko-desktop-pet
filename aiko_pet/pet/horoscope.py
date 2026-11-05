"""Immutable local horoscope facts, authored passages and pure selection."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

ZODIAC_SIGNS = (
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
)
RULES_REVISION = "solar-houses-v1"


class HoroscopeTheme(StrEnum):
    SELF = "self"
    RESOURCES = "resources"
    EXCHANGE = "exchange"
    HOME = "home"
    PLAY = "play"
    ROUTINE = "routine"
    ENCOUNTER = "encounter"
    CHANGE = "change"
    PERSPECTIVE = "perspective"
    GOALS = "goals"
    FRIENDSHIP = "friendship"
    REST = "rest"


class DevelopmentDirection(StrEnum):
    BEGIN = "begin"
    DEVELOP = "develop"
    REFLECT = "reflect"
    CONCLUDE = "conclude"


def normalized_angle(value: float) -> float:
    if isinstance(value, bool) or not math.isfinite(value):
        raise ValueError("An astronomical angle must be finite")
    return value % 360


def sign_at(longitude: float) -> str:
    return ZODIAC_SIGNS[int(normalized_angle(longitude) // 30)]


def relative_house(selected_sign: str, body_sign: str) -> int:
    if selected_sign not in ZODIAC_SIGNS or body_sign not in ZODIAC_SIGNS:
        raise ValueError("Unknown zodiac sign")
    return (ZODIAC_SIGNS.index(body_sign) - ZODIAC_SIGNS.index(selected_sign)) % 12 + 1


def phase_direction(phase_degrees: float) -> DevelopmentDirection:
    return tuple(DevelopmentDirection)[int(normalized_angle(phase_degrees) // 90)]


@dataclass(frozen=True, slots=True)
class SkySnapshot:
    instant_utc: datetime
    sun_longitude: float
    moon_longitude: float
    phase_degrees: float
    engine_version: str

    def __post_init__(self) -> None:
        if self.instant_utc.utcoffset() is None or not self.engine_version:
            raise ValueError("Sky facts require an aware instant and engine version")
        for angle in (self.sun_longitude, self.moon_longitude, self.phase_degrees):
            if not 0 <= normalized_angle(angle) == angle < 360:
                raise ValueError("Sky angles must be normalized")


@dataclass(frozen=True, slots=True)
class HoroscopeProfile:
    sign: str
    theme: HoroscopeTheme
    direction: DevelopmentDirection
    sun_sign: str
    moon_sign: str
    sun_house: int
    moon_house: int
    rules_revision: str = RULES_REVISION


def build_profile(selected_sign: str, sky: SkySnapshot) -> HoroscopeProfile:
    sun, moon = sign_at(sky.sun_longitude), sign_at(sky.moon_longitude)
    house = relative_house(selected_sign, moon)
    return HoroscopeProfile(
        selected_sign,
        tuple(HoroscopeTheme)[house - 1],
        phase_direction(sky.phase_degrees),
        sun,
        moon,
        relative_house(selected_sign, sun),
        house,
    )


@dataclass(frozen=True, slots=True)
class BookPassage:
    id: str
    text: str
    comment_key: str | None = None

    def __post_init__(self) -> None:
        if not self.id or not 1 <= len(self.text.strip()) <= 125:
            raise ValueError("Invalid complete book passage")
        if self.comment_key is not None and not self.comment_key:
            raise ValueError("Empty book comment key")


@dataclass(frozen=True, slots=True)
class EntryEligibility:
    sun_signs: tuple[str, ...] = ()
    moon_signs: tuple[str, ...] = ()
    sun_houses: tuple[int, ...] = ()
    moon_houses: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if any(
            sign not in ZODIAC_SIGNS for sign in (*self.sun_signs, *self.moon_signs)
        ):
            raise ValueError("Invalid astronomical sign restriction")
        if any(
            type(house) is not int or not 1 <= house <= 12
            for house in (*self.sun_houses, *self.moon_houses)
        ):
            raise ValueError("Invalid relative-house restriction")


@dataclass(frozen=True, slots=True)
class HoroscopeEntry:
    id: str
    revision: int
    theme: HoroscopeTheme
    direction: DevelopmentDirection
    variant: str
    allowed_signs: tuple[str, ...]
    passages: tuple[BookPassage, ...]
    eligibility: EntryEligibility = EntryEligibility()

    def __post_init__(self) -> None:
        if (
            not self.id
            or type(self.revision) is not int
            or self.revision < 1
            or self.variant not in ("a", "b")
            or not isinstance(self.theme, HoroscopeTheme)
            or not isinstance(self.direction, DevelopmentDirection)
        ):
            raise ValueError("Invalid horoscope entry identity")
        if (
            not self.allowed_signs
            or len(set(self.allowed_signs)) != len(self.allowed_signs)
            or any(sign not in ZODIAC_SIGNS for sign in self.allowed_signs)
        ):
            raise ValueError("Invalid reviewed sign applicability")
        if (
            not 1 <= len(self.passages) <= 8
            or len({p.id for p in self.passages}) != len(self.passages)
            or sum(p.comment_key is not None for p in self.passages) > 1
        ):
            raise ValueError("Invalid horoscope passage sequence")


@dataclass(frozen=True, slots=True)
class HoroscopeCatalogue:
    id: str
    revision: int
    entries: tuple[HoroscopeEntry, ...]

    def __post_init__(self) -> None:
        if (
            not self.id
            or type(self.revision) is not int
            or self.revision < 1
            or not self.entries
            or len({e.id for e in self.entries}) != len(self.entries)
        ):
            raise ValueError("Invalid local horoscope catalogue")


def entry_matches(entry: HoroscopeEntry, profile: HoroscopeProfile) -> bool:
    rule = entry.eligibility
    return (
        entry.theme == profile.theme
        and entry.direction == profile.direction
        and profile.sign in entry.allowed_signs
        and (not rule.sun_signs or profile.sun_sign in rule.sun_signs)
        and (not rule.moon_signs or profile.moon_sign in rule.moon_signs)
        and (not rule.sun_houses or profile.sun_house in rule.sun_houses)
        and (not rule.moon_houses or profile.moon_house in rule.moon_houses)
    )


def select_entry(
    catalogue: HoroscopeCatalogue,
    profile: HoroscopeProfile,
    selection_key: str,
) -> HoroscopeEntry | None:
    candidates = sorted(
        (entry for entry in catalogue.entries if entry_matches(entry, profile)),
        key=lambda entry: entry.id,
    )
    if not candidates:
        return None
    value = int.from_bytes(hashlib.sha256(selection_key.encode()).digest(), "big")
    return candidates[value % len(candidates)]
