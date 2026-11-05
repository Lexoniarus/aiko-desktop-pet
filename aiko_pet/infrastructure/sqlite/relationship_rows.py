"""Relationship facts use existing strict validation, never SQL reward rules."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...pet.friendship_history import NEED_NAMES, FriendshipHistory
from ..friendship_codec import decode_friendship, encode_friendship
from .rows import json_value, parse_json, read_rows, singleton, upsert_singleton


def write_friendship(
    connection: sqlite3.Connection, history: FriendshipHistory,
) -> None:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    raw = encode_friendship(history)
    decode_friendship(raw, elapsed)
    upsert_singleton(connection, "relationship_state", {
        "baseline": history.baseline, "last_contact": history.last_contact,
        "continuous_since": history.continuous_since,
        "eligible": json_value(dict(history.eligible)),
    })
    connection.execute("DELETE FROM relationship_entries")
    connection.execute("DELETE FROM need_exposure_buckets")
    categories = (("reward", history.rewards), ("penalty", history.penalties))
    for category, entries in categories:
        connection.executemany(
            "INSERT INTO relationship_entries VALUES (1, ?, ?, ?, ?, ?)",
            [(category, index, entry.at, entry.kind, entry.amount)
             for index, entry in enumerate(entries)],
        )
    connection.executemany(
        "INSERT INTO need_exposure_buckets VALUES (1, ?, ?, ?, ?, ?)",
        [(need, bucket.start, bucket.width, bucket.critical[index], bucket.zero[index])
         for bucket in history.critical for index, need in enumerate(NEED_NAMES)],
    )


def read_friendship(connection: sqlite3.Connection) -> FriendshipHistory:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    state = singleton(connection, "relationship_state")
    raw: dict[str, Any] = dict(
        version=1, baseline=state["baseline"], last_contact=state["last_contact"],
        continuous_since=state["continuous_since"],
        eligible=parse_json(state["eligible"]),
        rewards=[], penalties=[], critical=[],
    )
    for category, key in (("reward", "rewards"), ("penalty", "penalties")):
        rows = read_rows(connection,
                         "SELECT * FROM relationship_entries WHERE entry_kind = ? "
                         "ORDER BY position", (category,))
        for index, row in enumerate(rows):
            if row["position"] != index:
                raise ValueError("Relationship event order is incomplete")
            raw[key].append(dict(at=row["occurred_at"], kind=row["kind"],
                                 amount=row["amount"]))
    groups: dict[float, dict[str, dict[str, Any]]] = {}
    rows = read_rows(connection, "SELECT * FROM need_exposure_buckets ORDER BY start")
    for row in rows:
        groups.setdefault(row["start"], {})[row["need"]] = row
    for start, needs in groups.items():
        if set(needs) != set(NEED_NAMES):
            raise ValueError("Exposure bucket must retain all five named needs")
        widths = {row["width"] for row in needs.values()}
        if len(widths) != 1:
            raise ValueError("Per-need exposure intervals disagree")
        raw["critical"].append(dict(
            start=start, width=widths.pop(),
            critical=[needs[name]["critical"] for name in NEED_NAMES],
            zero=[needs[name]["zero"] for name in NEED_NAMES],
        ))
    return decode_friendship(raw, elapsed)
