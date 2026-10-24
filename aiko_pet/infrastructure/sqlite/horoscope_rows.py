"""Map the existing daily contract without HTTP, admission or replay decisions."""

from __future__ import annotations

import sqlite3

from ...application.horoscope_models import HoroscopeDay
from ..horoscope_codec import decode_horoscope, encode_horoscope
from .rows import boolean, read_rows, singleton

_READING_FIELDS = ("sign", "reading_date", "overview", "advice", "disclaimer", "footer")


def write_horoscope(connection: sqlite3.Connection, day: HoroscopeDay | None) -> None:
    singleton(connection, "save_state")
    raw = encode_horoscope(day)
    decode_horoscope(raw)
    connection.execute("DELETE FROM horoscope_days")
    if raw is None:
        return
    reading = raw["reading"]
    connection.execute(
        "INSERT INTO horoscope_days VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            raw["date"],
            raw["attempts"],
            raw["index"],
            int(raw["admitted"]),
            int(raw["completed"]),
            *(
                None
                if reading is None
                else reading["date" if name == "reading_date" else name]
                for name in _READING_FIELDS
            ),
        ),
    )


def read_horoscope(connection: sqlite3.Connection) -> HoroscopeDay | None:
    singleton(connection, "save_state")
    rows = read_rows(connection, "SELECT * FROM horoscope_days")
    if not rows:
        return None
    if len(rows) != 1:
        raise ValueError("Horoscope history must contain only the current day")
    row = rows[0]
    reading = (
        None
        if all(row[name] is None for name in _READING_FIELDS)
        else {
            "date" if name == "reading_date" else name: row[name]
            for name in _READING_FIELDS
        }
    )
    return decode_horoscope(
        dict(
            date=row["day"],
            attempts=row["attempts"],
            index=row["progress_index"],
            admitted=boolean(row["admitted"]),
            completed=boolean(row["completed"]),
            reading=reading,
        )
    )
