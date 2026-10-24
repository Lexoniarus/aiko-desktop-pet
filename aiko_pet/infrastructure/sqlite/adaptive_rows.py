"""Preserve adaptive memory without training on load or projecting closed time."""

import sqlite3

from ...pet.mind.adaptive_models import SLOTS, AdaptiveMemory
from ..adaptive_codec import (
    PROFILE_FIELDS,
    SCALAR_FIELDS,
    decode_adaptive,
    encode_adaptive,
)
from .rows import read_rows, singleton, upsert_singleton


def write_adaptive(connection: sqlite3.Connection, memory: AdaptiveMemory) -> None:
    raw = encode_adaptive(memory)
    decode_adaptive(raw)
    quiet = raw["quiet_window"]
    upsert_singleton(
        connection,
        "adaptive_state",
        {
            **{
                name: raw[name]
                for name in (*SCALAR_FIELDS, "last_slot_key", "profile_day")
            },
            "quiet_start": quiet["start"],
            "quiet_end": quiet["end"],
            "quiet_adjusted_day": quiet["adjusted_day"],
        },
    )
    connection.execute("DELETE FROM adaptive_hour_slots")
    connection.execute("DELETE FROM adaptive_quiet_phases")
    connection.executemany(
        "INSERT INTO adaptive_hour_slots VALUES (?, 1, ?, ?, ?, ?)",
        [
            (slot, *(raw[name][slot] for name in PROFILE_FIELDS))
            for slot in range(SLOTS)
        ],
    )
    connection.executemany(
        "INSERT INTO adaptive_quiet_phases VALUES (?, 1, ?, ?, ?)",
        [
            (phase["day"], index, phase["start"], phase["end"])
            for index, phase in enumerate(quiet["phases"])
        ],
    )


def read_adaptive(connection: sqlite3.Connection) -> AdaptiveMemory:
    state = singleton(connection, "adaptive_state")
    slots = read_rows(connection, "SELECT * FROM adaptive_hour_slots ORDER BY slot")
    if [row["slot"] for row in slots] != list(range(SLOTS)):
        raise ValueError("Adaptive hour-of-week profile is incomplete")
    phases = read_rows(
        connection, "SELECT * FROM adaptive_quiet_phases ORDER BY position_index"
    )
    if [row["position_index"] for row in phases] != list(range(len(phases))):
        raise ValueError("Adaptive quiet-phase order is incomplete")
    return decode_adaptive({
        **{
            name: state[name]
            for name in (*SCALAR_FIELDS, "last_slot_key", "profile_day")
        },
        **{name: [row[name] for row in slots] for name in PROFILE_FIELDS},
        "quiet_window": dict(
            version=1,
            start=state["quiet_start"],
            end=state["quiet_end"],
            adjusted_day=state["quiet_adjusted_day"],
            phases=[
                dict(day=row["day"], start=row["start"], end=row["end"])
                for row in phases
            ],
        ),
    })
