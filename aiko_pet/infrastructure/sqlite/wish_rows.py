"""Map wish core fields without generating, expiring, unpinning or fulfilling.

Handover facts are a separate owned part of WishState. Core replacement never
deletes them, and core reads retain the supplied template's handover values.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from typing import Any

from ...pet.wish_catalog import WISH_CATALOG
from ...pet.wish_types import WishId
from ...pet.wishes import WishState
from ..wish_codec import decode_wishes, encode_wishes
from .food_handover_rows import read_food_handovers, write_food_handovers
from .rows import (
    boolean,
    json_value,
    parse_json,
    read_rows,
    singleton,
    upsert_singleton,
)


def write_wish_core(connection: sqlite3.Connection, state: WishState) -> None:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    raw = encode_wishes(replace(state, food_handovers=()))
    decode_wishes(raw, elapsed)
    upsert_singleton(
        connection,
        "wish_state",
        {
            "next_instance_id": state.next_instance_id,
            "last_created_by_area": json_value(raw["last_created_by_area"]),
            "last_expressed_at": state.last_expressed_at,
            "refresh_at": state.refresh_at,
        },
    )
    connection.execute("DELETE FROM wish_instances")
    for index, wish in enumerate(raw["active"]):
        target, game = wish["target"], wish["game"]
        connection.execute(
            "INSERT INTO wish_instances VALUES "
            "(?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                wish["instance_id"],
                index,
                wish["definition_id"],
                WISH_CATALOG.definitions[WishId(wish["definition_id"])].area.value,
                wish["goal"]["objective"],
                wish["goal"]["required_count"],
                int(target is not None),
                None if target is None else target["kind"],
                None if target is None else target["mode"],
                wish["target_id"] if target is None else target["target_id"],
                wish["created_at"],
                wish["expires_at"],
                wish["expressed_at"],
                int(wish["pinned"]),
                game["completed_rounds"],
                game["wins"],
                game["losses"],
                game["session_id"],
            ),
        )
        connection.executemany(
            "INSERT INTO wish_round_receipts VALUES (?, ?, ?)",
            [
                (wish["instance_id"], position, signature)
                for position, signature in enumerate(game["round_ids"])
            ],
        )


def read_wish_core(
    connection: sqlite3.Connection,
    template: WishState = WishState(),
) -> WishState:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    state = singleton(connection, "wish_state")
    rounds: dict[int, list[str]] = {}
    for row in read_rows(
        connection, "SELECT * FROM wish_round_receipts ORDER BY wish_id, position_index"
    ):
        receipts = rounds.setdefault(row["wish_id"], [])
        if row["position_index"] != len(receipts):
            raise ValueError("Wish round evidence order is incomplete")
        receipts.append(row["round_signature"])
    active: list[dict[str, Any]] = []
    for row in read_rows(
        connection, "SELECT * FROM wish_instances ORDER BY position_index"
    ):
        if row["position_index"] != len(active):
            raise ValueError("Active wish order is incomplete")
        key = WishId(row["definition_id"])
        if row["area"] != WISH_CATALOG.definitions[key].area.value:
            raise ValueError("Saved wish area disagrees with its definition")
        target = (
            None
            if not boolean(row["target_explicit"])
            else dict(
                kind=row["target_kind"],
                mode=row["target_mode"],
                target_id=row["target_id"],
            )
        )
        active.append(
            dict(
                instance_id=row["instance_id"],
                definition_id=row["definition_id"],
                target_id=row["target_id"]
                if target is None
                else row["target_id"] or "",
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                expressed_at=row["expressed_at"],
                pinned=boolean(row["pinned"]),
                goal=dict(
                    objective=row["objective_id"], required_count=row["required_count"]
                ),
                target=target,
                game=dict(
                    round_ids=rounds.pop(row["instance_id"], []),
                    wins=row["wins"],
                    losses=row["losses"],
                    completed_rounds=row["completed_rounds"],
                    session_id=row["session_id"],
                ),
            )
        )
    if rounds:
        raise ValueError("Round evidence has no owning active wish")
    core = decode_wishes(
        dict(
            version=1,
            next_instance_id=state["next_instance_id"],
            active=active,
            last_created_by_area=parse_json(state["last_created_by_area"]),
            last_expressed_at=state["last_expressed_at"],
            refresh_at=state["refresh_at"],
        ),
        elapsed,
    )
    return replace(core, food_handovers=template.food_handovers)


def write_wishes(connection: sqlite3.Connection, state: WishState) -> None:
    """Validate the complete owned value before replacing either mapped part."""
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    decode_wishes(encode_wishes(state), elapsed)
    write_wish_core(connection, state)
    write_food_handovers(connection, state.food_handovers)


def read_wishes(connection: sqlite3.Connection) -> WishState:
    return replace(
        read_wish_core(connection), food_handovers=read_food_handovers(connection)
    )
