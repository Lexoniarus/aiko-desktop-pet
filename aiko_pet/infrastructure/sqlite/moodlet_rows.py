"""Episode storage only; shared boundary/evidence portions stay with their owners."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from typing import Any

from ...pet.interaction_events import InteractionMemory
from ...pet.moodlet_models import MoodletState
from ..moodlet_codec import decode_moodlets, encode_moodlets
from .moodlet_cause_rows import read_causes, write_causes
from .rows import boolean, read_rows, singleton, upsert_singleton

_EPISODE_FIELDS = (
    "instance_id",
    "definition_id",
    "level",
    "started_at",
    "last_trigger_at",
    "remaining_seconds",
    "pending_repetitions",
    "recovery_since",
    "attribution",
)


def write_moodlet_core(connection: sqlite3.Connection, state: MoodletState) -> None:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    raw = encode_moodlets(
        replace(
            state, interactions=InteractionMemory(), poor_care=None, care_evidence=None
        )
    )
    decode_moodlets(raw, elapsed)
    upsert_singleton(
        connection,
        "moodlet_state",
        {
            "baseline": state.baseline,
            "next_instance_id": state.next_instance_id,
        },
    )
    connection.execute("DELETE FROM moodlet_episodes")
    for index, episode in enumerate(raw["active"]):
        row = {name: episode[name] for name in _EPISODE_FIELDS}
        row.update(
            position_index=index,
            decay_paused=int(episode["decay_paused"]),
            lower_stages_explicit=int(bool(episode["lower_stage_seconds"])),
        )
        connection.execute(
            "INSERT INTO moodlet_episodes VALUES (:instance_id, 1, :position_index, "
            ":definition_id, :level, :started_at, :last_trigger_at, "
            ":remaining_seconds, "
            ":lower_stages_explicit, :pending_repetitions, :decay_paused, "
            ":recovery_since, :attribution)",
            row,
        )
        lower = dict(enumerate(episode["lower_stage_seconds"], start=1))
        relief = {
            stage: position for position, stage in enumerate(episode["relieved_levels"])
        }
        connection.executemany(
            "INSERT INTO moodlet_stage_state VALUES (?, ?, ?, ?)",
            [
                (episode["instance_id"], stage, lower.get(stage), relief.get(stage))
                for stage in sorted(lower.keys() | relief.keys())
            ],
        )
        write_causes(connection, episode["instance_id"], episode["causes"])


def read_moodlet_core(
    connection: sqlite3.Connection,
    template: MoodletState = MoodletState(),
) -> MoodletState:
    elapsed = singleton(connection, "save_state")["lived_seconds"]
    state = singleton(connection, "moodlet_state")
    causes = read_causes(connection)
    stages: dict[int, list[dict[str, Any]]] = {}
    for row in read_rows(connection, "SELECT * FROM moodlet_stage_state"):
        stages.setdefault(row["episode_id"], []).append(row)
    active: list[dict[str, Any]] = []
    for row in read_rows(
        connection, "SELECT * FROM moodlet_episodes ORDER BY position_index"
    ):
        if row["position_index"] != len(active):
            raise ValueError("Moodlet episode order is incomplete")
        owned = stages.pop(row["instance_id"], [])
        lower = {
            s["stage"]: s["lower_remaining_seconds"]
            for s in owned
            if s["lower_remaining_seconds"] is not None
        }
        expected = (
            set(range(1, row["level"]))
            if boolean(row["lower_stages_explicit"])
            else set()
        )
        if set(lower) != expected:
            raise ValueError("Moodlet lower-stage budgets are incomplete or unexpected")
        relief = sorted(
            (s["relief_position"], s["stage"])
            for s in owned
            if s["relief_position"] is not None
        )
        if [position for position, _ in relief] != list(range(len(relief))):
            raise ValueError("Moodlet relief order is incomplete")
        actual_causes = causes.pop(row["instance_id"], [])
        if not 1 <= len(actual_causes) <= row["level"]:
            raise ValueError(
                "Moodlet causes must retain the actual bounded stage history"
            )
        active.append(
            {name: row[name] for name in _EPISODE_FIELDS}
            | dict(
                decay_paused=boolean(row["decay_paused"]),
                lower_stage_seconds=[lower[stage] for stage in sorted(lower)],
                relieved_levels=[stage for _, stage in relief],
                causes=actual_causes,
            )
        )
    if stages or causes:
        raise ValueError("Moodlet child rows have no owning episode")
    core = decode_moodlets(
        dict(
            version=1,
            baseline=state["baseline"],
            next_instance_id=state["next_instance_id"],
            active=active,
        ),
        elapsed,
    )
    return replace(
        core,
        interactions=template.interactions,
        poor_care=template.poor_care,
        care_evidence=template.care_evidence,
    )
