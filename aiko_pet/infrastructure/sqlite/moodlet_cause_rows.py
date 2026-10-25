"""Small versioned cause details, independent of live wishes and raw evidence."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...pet.catalog_validation import object_fields
from .rows import json_value, parse_json, read_rows, require_transaction

_FACT_FIELDS = (
    "kind",
    "occurred_at",
    "event_id",
    "attribution",
    "target_id",
    "outcome",
    "object_id",
    "handed_over_at",
)


def write_causes(
    connection: sqlite3.Connection,
    episode_id: int,
    causes: list[dict[str, Any]],
) -> None:
    require_transaction(connection)
    for index, cause in enumerate(causes):
        wish = cause["wish"]
        details = dict(version=1, game=cause["game"], period=cause["period"])
        if cause.get("game_details") is not None:
            details.update(version=2, game_details=cause["game_details"])
        row = {name: cause[name] for name in _FACT_FIELDS}
        row.update(
            episode_id=episode_id,
            position_index=index,
            source_wish_instance_id=None if wish is None else wish["instance_id"],
            wish_snapshot=None
            if wish is None
            else json_value(dict(version=1, wish=wish)),
            details_snapshot=json_value(details),
        )
        connection.execute(
            "INSERT INTO moodlet_causes(episode_id, position_index, kind, occurred_at, "
            "event_id, attribution, target_id, outcome, object_id, handed_over_at, "
            "source_wish_instance_id, wish_snapshot, details_snapshot) VALUES "
            "(:episode_id, :position_index, :kind, :occurred_at, :event_id, "
            ":attribution, :target_id, :outcome, :object_id, :handed_over_at, "
            ":source_wish_instance_id, "
            ":wish_snapshot, :details_snapshot)",
            row,
        )


def _snapshot(raw: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    row = object_fields(parse_json(raw), ("version", *fields), context="Moodlet detail")
    if type(row["version"]) is not int or row["version"] != 1:
        raise ValueError("Unsupported Moodlet detail snapshot version")
    return row


def read_causes(connection: sqlite3.Connection) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in read_rows(
        connection, "SELECT * FROM moodlet_causes ORDER BY episode_id, position_index"
    ):
        causes = grouped.setdefault(row["episode_id"], [])
        if row["position_index"] != len(causes):
            raise ValueError("Moodlet cause order is incomplete")
        wish = (
            None
            if row["wish_snapshot"] is None
            else _snapshot(row["wish_snapshot"], ("wish",))["wish"]
        )
        if wish is not None and not isinstance(wish, dict):
            raise ValueError("Moodlet wish snapshot must contain original wish fields")
        if (None if wish is None else wish.get("instance_id")) != row[
            "source_wish_instance_id"
        ]:
            raise ValueError(
                "Moodlet source wish disagrees with its historical snapshot"
            )
        details = object_fields(
            parse_json(row["details_snapshot"]), ("version", "game", "period"),
            optional=("game_details",), context="Moodlet detail",
        )
        version = details["version"]
        if (type(version) is not int or version not in (1, 2)
                or (version == 2) != (details.get("game_details") is not None)
                or version == 1 and "game_details" in details):
            raise ValueError("Unsupported or inconsistent Moodlet detail snapshot")
        cause = {name: row[name] for name in _FACT_FIELDS} | dict(
            wish=wish, game=details["game"], period=details["period"],
        )
        if version == 2:
            cause["game_details"] = details["game_details"]
        causes.append(cause)
    return grouped
