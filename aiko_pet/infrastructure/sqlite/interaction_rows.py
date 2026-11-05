"""Preserve communicated boundaries and actual repeated-food intake evidence."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...pet.interaction_events import InteractionMemory
from ...pet.moodlet_models import MoodletState
from ..moodlet_codec import decode_moodlets, encode_moodlets
from .rows import boolean, read_rows, singleton, upsert_singleton

_MEMORY_FIELDS = (
    "poke_boundary_at",
    "petting_boundary_at",
    "petting_refused_until",
    "petting_excess_attempts",
    "petting_last_excess_at",
)


def _checked_memory(
    connection: sqlite3.Connection, raw: dict[str, Any]
) -> InteractionMemory:
    state = singleton(connection, "moodlet_state")
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    return decode_moodlets(
        dict(
            version=1,
            baseline=state["baseline"],
            next_instance_id=state["next_instance_id"],
            active=[],
            interactions=raw,
        ),
        elapsed,
    ).interactions


def write_interactions(
    connection: sqlite3.Connection, memory: InteractionMemory
) -> None:
    raw = encode_moodlets(MoodletState(interactions=memory))["interactions"]
    _checked_memory(connection, raw)
    food = raw["food"]
    upsert_singleton(
        connection,
        "interaction_state",
        {
            **{name: raw[name] for name in _MEMORY_FIELDS},
            "food_id": food["food_id"],
            "request_pending": int(food["request_pending"]),
            "requested_at": food["requested_at"],
            "ignored_portions": food["ignored_portions"],
        },
    )
    connection.execute("DELETE FROM food_intake_receipts")
    connection.executemany(
        "INSERT INTO food_intake_receipts VALUES (1, ?, ?)",
        list(enumerate(food["intakes"])),
    )


def read_interactions(connection: sqlite3.Connection) -> InteractionMemory:
    row = singleton(connection, "interaction_state")
    intakes = read_rows(
        connection, "SELECT * FROM food_intake_receipts ORDER BY position_index"
    )
    if [receipt["position_index"] for receipt in intakes] != list(range(len(intakes))):
        raise ValueError("Food intake evidence order is incomplete")
    return _checked_memory(
        connection,
        {name: row[name] for name in _MEMORY_FIELDS}
        | dict(
            food=dict(
                food_id=row["food_id"],
                intakes=[r["occurred_at"] for r in intakes],
                request_pending=boolean(row["request_pending"]),
                requested_at=row["requested_at"],
                ignored_portions=row["ignored_portions"],
            ),
        ),
    )
