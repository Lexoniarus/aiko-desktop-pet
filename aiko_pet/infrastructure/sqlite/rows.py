"""Small row operations inside the caller's coherent snapshot transaction."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from ...pet.catalog_validation import number_value

SqlValue = str | int | float | bytes | None


def require_transaction(connection: sqlite3.Connection) -> None:
    if not connection.in_transaction:
        raise ValueError("Snapshot mapping requires an explicit caller transaction")


def read_rows(
    connection: sqlite3.Connection, query: str, parameters: Sequence[SqlValue] = (),
) -> list[dict[str, Any]]:
    require_transaction(connection)
    cursor = connection.execute(query, parameters)
    assert cursor.description is not None
    names = tuple(column[0] for column in cursor.description)
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def singleton(connection: sqlite3.Connection, table: str) -> dict[str, Any]:
    if not table.isidentifier():
        raise ValueError("Invalid internal table identifier")
    rows = read_rows(connection, f"SELECT * FROM {table} WHERE id = 1")
    if len(rows) != 1:
        raise ValueError(f"Missing required snapshot record: {table}")
    return rows[0]


def upsert_singleton(
    connection: sqlite3.Connection, table: str, values: Mapping[str, SqlValue],
) -> None:
    require_transaction(connection)
    names = tuple(values)
    if not table.isidentifier() or any(not name.isidentifier() for name in names):
        raise ValueError("Invalid internal SQL identifier")
    columns = ", ".join(names)
    placeholders = ", ".join("?" for _ in names)
    updates = ", ".join(f"{name} = excluded.{name}" for name in names)
    connection.execute(
        f"INSERT INTO {table}(id, {columns}) VALUES (1, {placeholders}) "
        f"ON CONFLICT(id) DO UPDATE SET {updates}", tuple(values.values()),
    )


def json_value(value: Any) -> str:
    """Only bounded lists/maps selected by the owning mapper use this helper."""
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        raise ValueError("Saved list/map requires JSON text")

    def invalid_constant(token: str) -> Any:
        raise ValueError(f"Non-finite saved JSON value: {token}")

    return json.loads(value, parse_constant=invalid_constant)


def boolean(value: Any) -> bool:
    if type(value) is not int or value not in (0, 1):
        raise ValueError("Saved flag requires zero or one")
    return bool(value)


def nonnegative(value: Any, context: str) -> float:
    return number_value(value, minimum=0, maximum=float("inf"), context=context)
