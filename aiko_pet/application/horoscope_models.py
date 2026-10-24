"""Immutable horoscope request, validated-text and daily-progress values."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

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


def local_day(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).date().isoformat()


def checked_day(value: Any) -> str:
    if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
        raise ValueError("Invalid horoscope date")
    return value


@dataclass(frozen=True, slots=True)
class HoroscopeRequest:
    sign: str
    date: str


@dataclass(frozen=True, slots=True)
class HoroscopeText:
    sign: str
    date: str
    overview: str
    advice: str
    disclaimer: str
    footer: str


@dataclass(frozen=True, slots=True)
class HoroscopeDay:
    date: str
    attempts: int = 0
    reading: HoroscopeText | None = None
    index: int = 0
    admitted: bool = False
    completed: bool = False
