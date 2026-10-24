"""Processing positions into the one relationship exposure history, not a copy."""

from __future__ import annotations

import sqlite3

from ...pet.moodlet_models import PoorCareEvidence
from ..poor_care_codec import decode_poor_care, encode_poor_care
from .rows import boolean, read_rows, singleton


def write_poor_care(
    connection: sqlite3.Connection,
    evidence: PoorCareEvidence | None,
) -> None:
    state = singleton(connection, "moodlet_state")
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    raw = None if evidence is None else encode_poor_care(evidence)
    if raw is not None:
        decode_poor_care(raw, state["baseline"], elapsed)
    connection.execute(
        "UPDATE moodlet_state SET poor_care_baseline = ? WHERE id = 1",
        (None if evidence is None else evidence.baseline,),
    )
    connection.execute("DELETE FROM poor_care_cursors")
    if raw is not None:
        connection.executemany(
            "INSERT INTO poor_care_cursors VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    need,
                    row["accounted"]["at"],
                    row["accounted"]["critical"],
                    row["accounted"]["zero"],
                    row["handled"]["at"],
                    row["handled"]["critical"],
                    row["handled"]["zero"],
                    row["handled_level"],
                    int(row["exposed"]),
                )
                for need, row in raw["needs"].items()
            ],
        )


def read_poor_care(connection: sqlite3.Connection) -> PoorCareEvidence | None:
    state = singleton(connection, "moodlet_state")
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    rows = read_rows(connection, "SELECT * FROM poor_care_cursors")
    baseline = state["poor_care_baseline"]
    if baseline is None:
        if rows:
            raise ValueError("Uninitialized poor-care history cannot claim cursors")
        return None
    raw = dict(
        baseline=baseline,
        needs={
            row["need"]: dict(
                accounted=dict(
                    at=row["accounted_at"],
                    critical=row["accounted_critical"],
                    zero=row["accounted_zero"],
                ),
                handled=dict(
                    at=row["handled_at"],
                    critical=row["handled_critical"],
                    zero=row["handled_zero"],
                ),
                handled_level=row["handled_level"],
                exposed=boolean(row["exposed"]),
            )
            for row in rows
        },
    )
    return decode_poor_care(raw, state["baseline"], elapsed)
