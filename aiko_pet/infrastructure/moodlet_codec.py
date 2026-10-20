"""Versioned Moodlet storage on the existing pet elapsed axis; no ageing."""

from __future__ import annotations

from typing import Any

from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlets import (
    MoodletDecay,
    MoodletEpisode,
    MoodletId,
    MoodletState,
    PettingParameters,
    PokingParameters,
)


def decode_moodlets(raw: Any, elapsed: float) -> MoodletState:
    """Reject corrupt sections as a whole; callers retain unrelated pet values."""
    row = object_fields(raw, ("version", "baseline", "next_instance_id", "active"),
                        context="moodlets")
    if type(row["version"]) is not int or row["version"] != 1:
        raise ValueError("Unsupported saved Moodlet version")
    baseline = number_value(row["baseline"], minimum=0, maximum=elapsed,
                            context="moodlets.baseline")
    next_id = integer_value(row["next_instance_id"], minimum=1,
                            maximum=2**63 - 1, context="moodlets.next_instance_id")
    rows = row["active"]
    if not isinstance(rows, list) or len(rows) > len(MoodletId):
        raise ValueError("Unbounded Moodlet family collection")
    episodes: list[MoodletEpisode] = []
    instances: set[int] = set()
    families: set[MoodletId] = set()
    for value in rows:
        entry = object_fields(value, (
            "instance_id", "definition_id", "level", "started_at", "last_trigger_at",
            "remaining_seconds", "relieved_levels", "pending_repetitions",
            "decay_paused", "recovery_since",
        ), context="Moodlet episode")
        key = enum_value(entry["definition_id"], MoodletId, context="Moodlet family")
        definition = MOODLET_CATALOG.definitions[key]
        instance = integer_value(entry["instance_id"], minimum=1,
                                 maximum=next_id - 1, context="Moodlet instance")
        if key in families or instance in instances:
            raise ValueError("Duplicate Moodlet instance or family")
        level = integer_value(entry["level"], minimum=1,
                              maximum=len(definition.level_points),
                              context="Moodlet level")
        started = number_value(entry["started_at"], minimum=baseline,
                               maximum=elapsed, context="Moodlet start")
        trigger = number_value(entry["last_trigger_at"], minimum=started,
                               maximum=elapsed, context="Moodlet trigger")
        remaining = number_value(entry["remaining_seconds"], minimum=0,
                                 maximum=definition.decay_stage_seconds,
                                 context="Moodlet remaining stage")
        levels = entry["relieved_levels"]
        if not isinstance(levels, list) or len(levels) > len(definition.level_points):
            raise ValueError("Unbounded Moodlet relief usage")
        relieved = tuple(integer_value(v, minimum=1,
                                       maximum=len(definition.level_points),
                                       context="Moodlet relieved level")
                         for v in levels)
        if len(set(relieved)) != len(relieved) or (
            relieved and definition.relief_seconds == 0
        ):
            raise ValueError("Duplicate or ineligible Moodlet relief usage")
        parameters = definition.parameters
        repetitions = (
            parameters.escalation_pokes if isinstance(parameters, PokingParameters)
            else parameters.escalation_attempts
            if isinstance(parameters, PettingParameters) else 1
        )
        pending = integer_value(entry["pending_repetitions"], minimum=0,
                                maximum=repetitions - 1, context="Moodlet repetitions")
        if type(entry["decay_paused"]) is not bool:
            raise ValueError("Moodlet pause must be a boolean")
        recovery = (
            None if entry["recovery_since"] is None else number_value(
                entry["recovery_since"], minimum=started, maximum=elapsed,
                context="Moodlet recovery qualification",
            )
        )
        if definition.decay != MoodletDecay.STABLE_RECOVERY and recovery is not None:
            raise ValueError("Only poor-care Moodlets have stable recovery")
        if (definition.decay == MoodletDecay.QUIET_TIME and entry["decay_paused"]):
            raise ValueError("Quiet-time Moodlets cannot pause their ageing")
        episodes.append(MoodletEpisode(
            instance, key, level, started, trigger, remaining, relieved, pending,
            entry["decay_paused"], recovery,
        ))
        instances.add(instance)
        families.add(key)
    return MoodletState(baseline, next_id, tuple(episodes))


def valid_moodlets(raw: Any, elapsed: float) -> bool:
    try:
        decode_moodlets(raw, elapsed)
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def encode_moodlets(state: MoodletState) -> dict[str, Any]:
    return dict(
        version=1, baseline=state.baseline, next_instance_id=state.next_instance_id,
        active=[dict(
            instance_id=e.instance_id, definition_id=e.definition_id.value,
            level=e.level, started_at=e.started_at, last_trigger_at=e.last_trigger_at,
            remaining_seconds=e.remaining_seconds,
            relieved_levels=list(e.relieved_levels),
            pending_repetitions=e.pending_repetitions, decay_paused=e.decay_paused,
            recovery_since=e.recovery_since,
        ) for e in state.active],
    )
