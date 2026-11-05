"""Persist actual bounded evidence; never infer visits or qualify new periods."""

from __future__ import annotations

import sqlite3
from typing import Any

from ...pet.care_evidence import CareEvidenceState
from ..care_evidence_codec import decode_care_evidence, encode_care_evidence
from .rows import boolean, read_rows, singleton

_FLAGS = ("pleasant", "upsetting", "boundary_violated")


def write_care_evidence(
    connection: sqlite3.Connection,
    evidence: CareEvidenceState | None,
) -> None:
    state = singleton(connection, "moodlet_state")
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    raw = None if evidence is None else encode_care_evidence(evidence)
    if raw is not None:
        decode_care_evidence(raw, state["baseline"], elapsed)
    connection.execute(
        "UPDATE moodlet_state SET care_evidence_baseline = ?, next_encounter_id = ?, "
        "next_experience_id = ? WHERE id = 1",
        (None, None, None)
        if evidence is None
        else (
            evidence.baseline,
            evidence.next_encounter_id,
            evidence.next_experience_id,
        ),
    )
    # A retained receipt protects its actual encounter: clear receipts first.
    for table in ("care_evidence", "care_encounters", "long_term_progress"):
        connection.execute(f"DELETE FROM {table}")
    if raw is None:
        return
    connection.executemany(
        "INSERT INTO care_encounters VALUES (?, 1, ?, ?, ?)",
        [
            (row["instance_id"], index, row["started_at"], row["last_activity_at"])
            for index, row in enumerate(raw["encounters"])
        ],
    )
    for index, experience in enumerate(raw["experiences"]):
        row = dict(experience, position_index=index)
        row.update((name, int(row[name])) for name in _FLAGS)
        connection.execute(
            "INSERT INTO care_evidence VALUES (:receipt_id, 1, :position_index, "
            ":occurred_at, :activity, :outcome, :area, :target_kind, :target_id, "
            ":encounter_id, :wish_instance_id, :pleasant, :upsetting, "
            ":boundary_violated, :object_id)",
            row,
        )
    for index, progress in enumerate(raw["progress"]):
        connection.execute(
            "INSERT INTO long_term_progress VALUES (:definition_id, 1, "
            ":position_index, "
            ":period_start, :processed_until, :last_accounted_at, "
            ":awake_contact_gap_seconds, :longest_awake_contact_gap_seconds)",
            dict(progress, position_index=index),
        )


def _ordered_values(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    values = read_rows(connection, f"SELECT * FROM {table} ORDER BY position_index")
    for index, value in enumerate(values):
        if value.pop("position_index") != index:
            raise ValueError("Care evidence order is incomplete")
        del value["state_id"]
    return values


def read_care_evidence(connection: sqlite3.Connection) -> CareEvidenceState | None:
    state = singleton(connection, "moodlet_state")
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    raw: dict[str, Any] = dict(
        version=1,
        baseline=state["care_evidence_baseline"],
        next_encounter_id=state["next_encounter_id"],
        next_experience_id=state["next_experience_id"],
        encounters=_ordered_values(connection, "care_encounters"),
        experiences=_ordered_values(connection, "care_evidence"),
        progress=_ordered_values(connection, "long_term_progress"),
    )
    if raw["baseline"] is None:
        if any(raw[key] for key in ("encounters", "experiences", "progress")) or any(
            raw[key] is not None for key in ("next_encounter_id", "next_experience_id")
        ):
            raise ValueError(
                "Uninitialized care history cannot claim evidence or counters"
            )
        return None
    for row in raw["experiences"]:
        row.update((name, boolean(row[name])) for name in _FLAGS)
    return decode_care_evidence(raw, state["baseline"], elapsed)
