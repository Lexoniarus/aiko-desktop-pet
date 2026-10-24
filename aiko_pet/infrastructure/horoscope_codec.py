"""Strict bounded extension of the existing atomic social-history snapshot."""

from dataclasses import asdict
from typing import Any

from ..application.horoscope import prepare_horoscope_text
from ..application.horoscope_models import HoroscopeDay, HoroscopeText, checked_day
from ..pet.catalog_validation import object_fields


def decode_horoscope(raw: Any) -> HoroscopeDay | None:
    if raw is None:
        return None
    row = object_fields(
        raw,
        ("date", "attempts", "reading", "index", "admitted", "completed"),
        context="daily horoscope",
    )
    day = checked_day(row["date"])
    attempts, index = row["attempts"], row["index"]
    if (
        type(attempts) is not int
        or not 0 <= attempts <= 3
        or type(index) is not int
        or not 0 <= index <= 12
        or type(row["admitted"]) is not bool
        or type(row["completed"]) is not bool
    ):
        raise ValueError("Invalid horoscope progress")
    reading = None
    if row["reading"] is not None:
        text = object_fields(
            row["reading"],
            ("date", "sign", "overview", "advice", "disclaimer", "footer"),
            context="horoscope text",
        )
        if any(not isinstance(v, str) for v in text.values()):
            raise ValueError("Invalid cached horoscope text")
        reading = HoroscopeText(**text)
        count = len(prepare_horoscope_text(reading).reaction.beats)
        if reading.date != day or not attempts or index > count:
            raise ValueError("Mismatched horoscope record")
        if row["completed"] != (index == count):
            raise ValueError("Inconsistent horoscope completion")
    if (
        (reading is None and (index or row["admitted"] or row["completed"]))
        or not row["admitted"]
        and (index or row["completed"])
    ):
        raise ValueError("Unadmitted horoscope progress")
    return HoroscopeDay(
        day, attempts, reading, index, row["admitted"], row["completed"]
    )


def encode_horoscope(day: HoroscopeDay | None) -> dict[str, Any] | None:
    return asdict(day) if day is not None else None
