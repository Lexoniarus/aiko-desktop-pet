"""Bounded local reading snapshots and one-way migration of rejected API data."""

from __future__ import annotations

import math
from dataclasses import asdict
from datetime import datetime
from typing import Any

from ..application.horoscope_models import (
    HoroscopeDay,
    HoroscopeHistory,
    PreparedBookReading,
    checked_day,
)
from ..pet.catalog_validation import object_fields
from ..pet.horoscope import SkySnapshot
from ..pet.mind.catalog import Reaction
from ..pet.mind.reaction_sequence import Cue


def _reading(raw: Any) -> PreparedBookReading:
    row = object_fields(
        raw,
        (
            "date",
            "sign",
            "entry_id",
            "entry_revision",
            "catalogue_revision",
            "comment_id",
            "sky",
            "reaction",
        ),
        context="saved book reading",
    )
    reaction = object_fields(
        row["reaction"], ("id", "beats"), context="saved reading cues"
    )
    if (
        not isinstance(reaction["id"], str)
        or not isinstance(reaction["beats"], list)
        or not 1 <= len(reaction["beats"]) <= 40
    ):
        raise ValueError("Invalid saved book sequence")
    beats: list[Cue] = []
    for value in reaction["beats"]:
        cue = object_fields(
            value, ("kind", "content", "duration_ms"), context="saved cue"
        )
        if cue["kind"] not in ("text", "emote", "pause") or not isinstance(
            cue["content"], str
        ):
            raise ValueError("Invalid saved cue")
        beats.append(Cue(cue["kind"], cue["content"], cue["duration_ms"]))
    sky = None
    if row["sky"] is not None:
        data = object_fields(
            row["sky"],
            (
                "instant_utc",
                "sun_longitude",
                "moon_longitude",
                "phase_degrees",
                "engine_version",
            ),
            context="saved sky",
        )
        sky = SkySnapshot(
            datetime.fromisoformat(data["instant_utc"]),
            data["sun_longitude"],
            data["moon_longitude"],
            data["phase_degrees"],
            data["engine_version"],
        )
    if any(
        not isinstance(row[k], str) for k in ("date", "sign", "entry_id", "comment_id")
    ):
        raise ValueError("Invalid reading identity")
    return PreparedBookReading(
        row["date"],
        row["sign"],
        row["entry_id"],
        row["entry_revision"],
        row["catalogue_revision"],
        Reaction(
            reaction["id"],
            tuple(beats),
            "idle",
            "horoscope_reading",
            presentation="story",
        ),
        row["comment_id"],
        sky,
    )


def _day(raw: Any) -> HoroscopeDay:
    row = object_fields(
        raw,
        (
            "date",
            "sign",
            "reading",
            "index",
            "admitted",
            "completed",
            "book_instance_id",
            "first_put_down_at",
        ),
        context="saved horoscope day",
    )
    checked_day(row["date"])
    if (
        type(row["index"]) is not int
        or row["index"] < 0
        or type(row["admitted"]) is not bool
        or type(row["completed"]) is not bool
        or row["completed"]
        and not row["admitted"]
        or row["book_instance_id"] is not None
        and (
            not isinstance(row["book_instance_id"], str) or not row["book_instance_id"]
        )
    ):
        raise ValueError("Invalid reading progress")
    reading = None if row["reading"] is None else _reading(row["reading"])
    if reading is not None:
        if (
            reading.date != row["date"]
            or reading.sign != row["sign"]
            or not row["admitted"]
            or not row["book_instance_id"]
            or row["index"] > len(reading.reaction.beats)
        ):
            raise ValueError("Mismatched frozen book episode")
    elif row["index"] or row["book_instance_id"]:
        raise ValueError("Legacy marker cannot invent local progress")
    deadline = row["first_put_down_at"]
    if deadline is not None and (
        type(deadline) not in (int, float)
        or not math.isfinite(deadline)
        or deadline < 0
        or not row["completed"]
        or reading is None
    ):
        raise ValueError("Invalid first book put-down timestamp")
    return HoroscopeDay(
        row["date"],
        row["sign"],
        reading,
        row["index"],
        row["admitted"],
        row["completed"],
        row["book_instance_id"],
        deadline,
    )


def migrate_legacy_horoscope(raw: Any) -> HoroscopeHistory:
    if raw is None:
        return HoroscopeHistory()
    row = object_fields(
        raw,
        ("date", "attempts", "reading", "index", "admitted", "completed"),
        context="legacy API horoscope",
    )
    checked_day(row["date"])
    if (
        type(row["attempts"]) is not int
        or not 0 <= row["attempts"] <= 3
        or type(row["index"]) is not int
        or not 0 <= row["index"] <= 12
        or type(row["admitted"]) is not bool
        or type(row["completed"]) is not bool
        or row["completed"]
        and not row["admitted"]
    ):
        raise ValueError("Invalid legacy horoscope marker")
    sign = None
    if row["reading"] is not None:
        text = object_fields(
            row["reading"],
            (
                "date",
                "sign",
                "overview",
                "advice",
                "disclaimer",
                "footer",
            ),
            context="legacy provider text",
        )
        if any(not isinstance(v, str) or len(v) > 10000 for v in text.values()):
            raise ValueError("Invalid legacy provider text")
        if text["date"] != row["date"]:
            raise ValueError("Mismatched legacy date")
        sign = text["sign"]
    elif row["admitted"] or row["index"]:
        raise ValueError("Unbacked legacy admission")
    return (
        HoroscopeHistory((
            HoroscopeDay(
                row["date"],
                sign,
                admitted=row["admitted"],
                completed=row["completed"],
            ),
        ))
        if row["admitted"]
        else HoroscopeHistory()
    )


def decode_horoscope(raw: Any) -> HoroscopeHistory:
    if raw is None:
        return HoroscopeHistory()
    if isinstance(raw, dict) and "version" not in raw:
        return migrate_legacy_horoscope(raw)
    data = object_fields(raw, ("version", "days"), context="local horoscope history")
    if (
        type(data["version"]) is not int
        or data["version"] != 1
        or not isinstance(data["days"], list)
    ):
        raise ValueError("Unsupported local horoscope history")
    return HoroscopeHistory(tuple(_day(day) for day in data["days"]))


def encode_horoscope(history: HoroscopeHistory) -> dict[str, Any]:
    days: list[dict[str, Any]] = []
    for day in history.days:
        row = asdict(day)
        if day.reading is not None:
            reading = day.reading
            sky = asdict(reading.sky) if reading.sky is not None else None
            if sky is not None:
                sky["instant_utc"] = reading.sky.instant_utc.isoformat()  # type: ignore[union-attr]
            row["reading"] = dict(
                date=reading.date,
                sign=reading.sign,
                entry_id=reading.entry_id,
                entry_revision=reading.entry_revision,
                catalogue_revision=reading.catalogue_revision,
                comment_id=reading.comment_id,
                sky=sky,
                reaction=dict(
                    id=reading.reaction.line_id,
                    beats=[asdict(cue) for cue in reading.reaction.beats],
                ),
            )
        days.append(row)
    return dict(version=1, days=days)
