"""Store original personal-transfer context without recognition or rewards."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...pet.catalog_validation import object_fields
from ...pet.food_handover import FoodHandoverReceipt
from ..food_handover_codec import decode_food_handovers, encode_food_handovers
from .rows import json_value, parse_json, read_rows, singleton

_FACT_FIELDS = (
    "handover_id",
    "object_id",
    "handed_over_at",
    "recognized_food_id",
    "recognized_at",
    "status",
    "resolved_wish_instance_id",
)


def write_food_handovers(
    connection: sqlite3.Connection,
    receipts: tuple[FoodHandoverReceipt, ...],
) -> None:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    next_id = singleton(connection, "wish_state")["next_instance_id"]
    raw = encode_food_handovers(receipts)
    decode_food_handovers(raw, elapsed, next_id)
    connection.execute("DELETE FROM food_handover_receipts")
    for index, receipt in enumerate(raw):
        row = {name: receipt[name] for name in _FACT_FIELDS}
        row.update(
            position_index=index,
            wish_context=json_value(dict(version=1, wishes=receipt["wishes"])),
            accounted_wish_ids=json_value(receipt["accounted_wish_ids"]),
        )
        connection.execute(
            "INSERT INTO food_handover_receipts "
            "(handover_id, state_id, position_index, object_id, handed_over_at, "
            "wish_context, recognized_food_id, recognized_at, status, "
            "resolved_wish_instance_id, accounted_wish_ids) VALUES "
            "(:handover_id, 1, :position_index, :object_id, :handed_over_at, "
            ":wish_context, :recognized_food_id, :recognized_at, :status, "
            ":resolved_wish_instance_id, :accounted_wish_ids)",
            row,
        )


def read_food_handovers(
    connection: sqlite3.Connection,
) -> tuple[FoodHandoverReceipt, ...]:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    next_id = singleton(connection, "wish_state")["next_instance_id"]
    raw: list[dict[str, Any]] = []
    for row in read_rows(
        connection, "SELECT * FROM food_handover_receipts ORDER BY position_index"
    ):
        if row["position_index"] != len(raw):
            raise ValueError("Food handover order is incomplete")
        context = object_fields(
            parse_json(row["wish_context"]),
            ("version", "wishes"),
            context="saved handover wish snapshot",
        )
        if type(context["version"]) is not int or context["version"] != 1:
            raise ValueError("Unsupported handover wish snapshot version")
        raw.append(
            {name: row[name] for name in _FACT_FIELDS}
            | dict(
                wishes=context["wishes"],
                accounted_wish_ids=parse_json(row["accounted_wish_ids"]),
            )
        )
    return decode_food_handovers(raw, elapsed, next_id)
