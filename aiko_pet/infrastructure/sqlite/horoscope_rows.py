"""Map local reading snapshots and cues in the caller's session transaction."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...application.horoscope_models import HoroscopeHistory
from ..horoscope_codec import decode_horoscope, encode_horoscope
from .rows import boolean, read_rows, singleton

_FIELDS = (
    "day",
    "state_id",
    "sign",
    "progress_index",
    "admitted",
    "completed",
    "book_id",
    "first_put_down_at",
    "entry_id",
    "entry_revision",
    "catalogue_revision",
    "reaction_id",
    "comment_id",
    "sky_instant",
    "sun_longitude",
    "moon_longitude",
    "phase_degrees",
    "engine_version",
)


def write_horoscope(connection: sqlite3.Connection, history: HoroscopeHistory) -> None:
    singleton(connection, "save_state")
    raw = encode_horoscope(history)
    decode_horoscope(raw)
    connection.execute("DELETE FROM local_horoscope_days")
    for day in raw["days"]:
        reading = day["reading"]
        sky = reading["sky"] if reading is not None else None
        values = (
            day["date"],
            1,
            day["sign"],
            day["index"],
            int(day["admitted"]),
            int(day["completed"]),
            day["book_instance_id"],
            day["first_put_down_at"],
            *(
                reading[k] if reading is not None else None
                for k in ("entry_id", "entry_revision", "catalogue_revision")
            ),
            reading["reaction"]["id"] if reading is not None else None,
            reading["comment_id"] if reading is not None else None,
            *(
                sky[k] if sky is not None else None
                for k in (
                    "instant_utc",
                    "sun_longitude",
                    "moon_longitude",
                    "phase_degrees",
                    "engine_version",
                )
            ),
        )
        connection.execute(
            f"INSERT INTO local_horoscope_days({','.join(_FIELDS)}) "
            f"VALUES ({','.join('?' for _ in _FIELDS)})",
            values,
        )
        if reading is not None:
            connection.executemany(
                "INSERT INTO local_horoscope_cues VALUES (?,?,?,?,?)",
                [
                    (day["date"], i, cue["kind"], cue["content"], cue["duration_ms"])
                    for i, cue in enumerate(reading["reaction"]["beats"])
                ],
            )


def read_horoscope(connection: sqlite3.Connection) -> HoroscopeHistory:
    singleton(connection, "save_state")
    days: list[dict[str, Any]] = []
    for row in read_rows(connection, "SELECT * FROM local_horoscope_days ORDER BY day"):
        reading = None
        if row["entry_id"] is not None:
            cues = read_rows(
                connection,
                "SELECT position_index,kind,content,duration_ms "
                "FROM local_horoscope_cues WHERE day=? ORDER BY position_index",
                (row["day"],),
            )
            for i, cue in enumerate(cues):
                if cue.pop("position_index") != i:
                    raise ValueError("Reading cue order has a gap")
            sky = (
                None
                if row["sky_instant"] is None
                else dict(
                    instant_utc=row["sky_instant"],
                    sun_longitude=row["sun_longitude"],
                    moon_longitude=row["moon_longitude"],
                    phase_degrees=row["phase_degrees"],
                    engine_version=row["engine_version"],
                )
            )
            reading = dict(
                date=row["day"],
                sign=row["sign"],
                entry_id=row["entry_id"],
                entry_revision=row["entry_revision"],
                catalogue_revision=row["catalogue_revision"],
                comment_id=row["comment_id"],
                sky=sky,
                reaction=dict(id=row["reaction_id"], beats=cues),
            )
        days.append(
            dict(
                date=row["day"],
                sign=row["sign"],
                reading=reading,
                index=row["progress_index"],
                admitted=boolean(row["admitted"]),
                completed=boolean(row["completed"]),
                book_instance_id=row["book_id"],
                first_put_down_at=row["first_put_down_at"],
            )
        )
    return decode_horoscope(dict(version=1, days=days))
