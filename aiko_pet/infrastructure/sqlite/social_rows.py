"""Map existing social receipts/limits; horoscope is independently owned state."""

import sqlite3
from typing import Any

from ...application.social_history import SocialContentHistory
from ..social_history_codec import decode_social_history, encode_social_history
from .rows import read_rows, singleton


def write_social_core(
    connection: sqlite3.Connection, history: SocialContentHistory
) -> None:
    singleton(connection, "save_state")
    raw = encode_social_history(history)
    decode_social_history(raw)
    for table in ("social_receipts", "social_requests", "provider_pauses",
                  "joke_exclusions"):
        connection.execute(f"DELETE FROM {table}")
    connection.executemany(
        "INSERT INTO joke_exclusions VALUES (?, 1, ?, ?, ?, ?, ?, ?)",
        [(index, row["category"], row["lower"], row["upper"], row["reason"],
          row["until"], row["revision"])
         for index, row in enumerate(raw["exclusions"])],
    )
    connection.executemany(
        "INSERT INTO social_receipts VALUES (?, 1, ?, ?, ?, ?)",
        [
            (
                index,
                row["category"],
                row["identity"],
                row["fingerprint"],
                row["intro_variant"],
            )
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
            version=6,
            exclusions=_ordered(connection, "joke_exclusions"),
            entries=_ordered(connection, "social_receipts"),
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
    return history


def write_social_history(
    connection: sqlite3.Connection,
    history: SocialContentHistory,
) -> None:
    singleton(connection, "save_state")
    decode_social_history(encode_social_history(history))
    write_social_core(connection, history)


def read_social_history(connection: sqlite3.Connection) -> SocialContentHistory:
    return read_social_core(connection)
