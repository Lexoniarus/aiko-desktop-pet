"""Map existing social receipts/limits; horoscope is independently owned state."""

import sqlite3
from dataclasses import replace
from typing import Any

from ...application.social_history import SocialContentHistory
from ..social_history_codec import decode_social_history, encode_social_history
from .rows import read_rows, singleton


def write_social_core(
    connection: sqlite3.Connection, history: SocialContentHistory
) -> None:
    singleton(connection, "save_state")
    raw = encode_social_history(replace(history, horoscope=None))
    decode_social_history(raw)
    for table in ("social_receipts", "social_requests", "provider_pauses"):
        connection.execute(f"DELETE FROM {table}")
    connection.executemany(
        "INSERT INTO social_receipts VALUES (?, 1, ?, ?, ?)",
        [
            (index, row["category"], row["identity"], row["fingerprint"])
            for index, row in enumerate(raw["entries"])
        ],
    )
    connection.executemany(
        "INSERT INTO social_requests VALUES (?, 1, ?, ?)",
        [
            (index, row["provider"], row["at"])
            for index, row in enumerate(raw["requests"]["attempts"])
        ],
    )
    connection.executemany(
        "INSERT INTO provider_pauses VALUES (?, 1, ?, ?)",
        [
            (row["provider"], index, row["until"])
            for index, row in enumerate(raw["requests"]["blocks"])
        ],
    )


def _ordered(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    rows = read_rows(connection, f"SELECT * FROM {table} ORDER BY position_index")
    for index, row in enumerate(rows):
        if row.pop("position_index") != index:
            raise ValueError("Social receipt order is incomplete")
        del row["state_id"]
    return rows


def read_social_core(
    connection: sqlite3.Connection,
    template: SocialContentHistory = SocialContentHistory(),
) -> SocialContentHistory:
    singleton(connection, "save_state")
    history = decode_social_history(
        dict(
            version=3,
            entries=_ordered(connection, "social_receipts"),
            horoscope=None,
            requests=dict(
                attempts=[
                    dict(provider=row["provider"], at=row["attempted_at"])
                    for row in _ordered(connection, "social_requests")
                ],
                blocks=[
                    dict(provider=row["provider"], until=row["pause_until"])
                    for row in _ordered(connection, "provider_pauses")
                ],
            ),
        )
    )
    return replace(history, horoscope=template.horoscope)
