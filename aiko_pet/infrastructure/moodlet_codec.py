"""Versioned Moodlet storage on the existing pet elapsed axis; no ageing."""

from __future__ import annotations

from typing import Any

from ..pet.balance import BALANCE
from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.interaction_events import FoodRepetitionMemory, InteractionMemory
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlet_models import CursorImpressionParameters
from ..pet.moodlets import (
    FoodMonotonyParameters,
    MoodletAttribution,
    MoodletDecay,
    MoodletEpisode,
    MoodletId,
    MoodletState,
    PettingParameters,
    PokingParameters,
)
from .care_evidence_codec import decode_care_evidence, encode_care_evidence
from .moodlet_cause_codec import decode_moodlet_causes, encode_moodlet_cause
from .poor_care_codec import decode_poor_care, encode_poor_care


def decode_moodlets(raw: Any, elapsed: float) -> MoodletState:
    """Reject corrupt sections as a whole; callers retain unrelated pet values."""
    row = object_fields(raw, ("version", "baseline", "next_instance_id", "active"),
                        optional=("interactions", "poor_care", "care_evidence"),
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
        ), optional=("attribution", "causes", "lower_stage_seconds"),
            context="Moodlet episode")
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
        staged_positive = definition.uses_explicit_stage_budgets
        cursor_profile = definition.parameters
        cap = (max(cursor_profile.stage_seconds)
               if isinstance(cursor_profile, CursorImpressionParameters)
               else BALANCE.integer("moodlets", "positive_stage_cap_seconds"))
        remaining = number_value(entry["remaining_seconds"], minimum=0,
                                 maximum=max(definition.decay_stage_seconds,
                                             cap if staged_positive else 0),
                                 context="Moodlet remaining stage")
        lower_raw = entry.get("lower_stage_seconds", [])
        if (not isinstance(lower_raw, list)
                or lower_raw and (not staged_positive or len(lower_raw) != level - 1)):
            raise ValueError("Incompatible lower Moodlet stage budgets")
        lower = tuple(number_value(v, minimum=0, maximum=cap,
                                   context="lower Moodlet stage remaining")
                      for v in lower_raw)
        if isinstance(cursor_profile, CursorImpressionParameters):
            if (remaining > cursor_profile.stage_seconds[level - 1]
                    or len(lower) != level - 1
                    or any(v > cursor_profile.stage_seconds[i]
                           for i, v in enumerate(lower))):
                raise ValueError("Invalid cursor stage budgets")
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
        causes = (decode_moodlet_causes(
            entry["causes"], started=started, trigger=trigger, key=key,
            baseline=baseline,
        ) if "causes" in entry else ())
        episodes.append(MoodletEpisode(
            instance, key, level, started, trigger, remaining, relieved, pending,
            entry["decay_paused"], recovery,
            enum_value(entry.get("attribution", "unknown"), MoodletAttribution,
                       context="Moodlet attribution"),
            causes, lower,
        ))
        instances.add(instance)
        families.add(key)
    memory = InteractionMemory()
    if "interactions" in row:
        facts = object_fields(row["interactions"], (
            "poke_boundary_at", "petting_boundary_at", "petting_refused_until",
        ), optional=("food", "petting_excess_attempts", "petting_last_excess_at"),
            context="interaction evidence")
        anchors = tuple(None if facts[key] is None else number_value(
            facts[key], minimum=baseline, maximum=elapsed, context=key,
        ) for key in ("poke_boundary_at", "petting_boundary_at"))
        petting = MOODLET_CATALOG.definitions[MoodletId.CROWDED].parameters
        assert isinstance(petting, PettingParameters)
        deadline = number_value(facts["petting_refused_until"], minimum=0,
                                maximum=elapsed + max(petting.refusal_seconds),
                                context="petting refusal")
        food = (_decode_food(facts["food"], baseline, elapsed)
                if "food" in facts else FoodRepetitionMemory())
        attempts = integer_value(
            facts.get("petting_excess_attempts",
                      petting.accepted_excess_attempts + 1 if anchors[1] is not None
                      else 0), minimum=0, maximum=petting.accepted_excess_attempts + 1,
            context="petting additional attempts",
        )
        last = facts.get("petting_last_excess_at", anchors[1])
        last = (None if last is None else number_value(
            last, minimum=baseline, maximum=elapsed, context="last additional petting",
        ))
        if (attempts == 0) != (last is None):
            raise ValueError("Petting count and time must describe the same sequence")
        memory = InteractionMemory(anchors[0], anchors[1], deadline, food,
                                   attempts, last)
    poor_care = (decode_poor_care(row["poor_care"], baseline, elapsed)
                 if "poor_care" in row else None)
    evidence = (None if "care_evidence" not in row else
                decode_care_evidence(row["care_evidence"], baseline, elapsed))
    return MoodletState(baseline, next_id, tuple(episodes), memory, poor_care, evidence)


def valid_moodlets(raw: Any, elapsed: float) -> bool:
    try:
        decode_moodlets(raw, elapsed)
    except (ValueError, TypeError, OverflowError):
        return False
    return True


def encode_moodlets(state: MoodletState) -> dict[str, Any]:
    encoded = dict(
        version=1, baseline=state.baseline, next_instance_id=state.next_instance_id,
        interactions=dict(
            poke_boundary_at=state.interactions.poke_boundary_at,
            petting_boundary_at=state.interactions.petting_boundary_at,
            petting_refused_until=state.interactions.petting_refused_until,
            petting_excess_attempts=state.interactions.petting_excess_attempts,
            petting_last_excess_at=state.interactions.petting_last_excess_at,
            food=dict(
                food_id=state.interactions.food.food_id,
                intakes=list(state.interactions.food.intakes),
                request_pending=state.interactions.food.request_pending,
                requested_at=state.interactions.food.requested_at,
                ignored_portions=state.interactions.food.ignored_portions,
            ),
        ),
        active=[dict(
            instance_id=e.instance_id, definition_id=e.definition_id.value,
            level=e.level, started_at=e.started_at, last_trigger_at=e.last_trigger_at,
            remaining_seconds=e.remaining_seconds,
            lower_stage_seconds=list(e.lower_stage_seconds),
            relieved_levels=list(e.relieved_levels),
            pending_repetitions=e.pending_repetitions, decay_paused=e.decay_paused,
            recovery_since=e.recovery_since,
            attribution=e.attribution.value,
            causes=[encode_moodlet_cause(c) for c in e.causes],
        ) for e in state.active],
    )
    if state.poor_care is not None:
        encoded["poor_care"] = encode_poor_care(state.poor_care)
    if state.care_evidence is not None:
        encoded["care_evidence"] = encode_care_evidence(state.care_evidence)
    return encoded


def _decode_food(raw: Any, baseline: float, elapsed: float) -> FoodRepetitionMemory:
    row = object_fields(raw, ("food_id", "intakes", "request_pending", "requested_at",
                              "ignored_portions"), context="food repetition evidence")
    food = row["food_id"]
    if food is not None and (
        not isinstance(food, str) or food not in DEFAULT_CATALOG.foods
    ):
        raise ValueError("Unknown repetition food")
    count = BALANCE.integer("food", "consecutive_repeats_before_dislike") + 1
    if not isinstance(row["intakes"], list) or len(row["intakes"]) > count:
        raise ValueError("Unbounded food repetition history")
    intakes = tuple(number_value(t, minimum=baseline, maximum=elapsed,
                                 context="food intake") for t in row["intakes"])
    if tuple(sorted(intakes)) != intakes:
        raise ValueError("Unordered food intake evidence")
    if type(row["request_pending"]) is not bool:
        raise ValueError("Food request pending must be boolean")
    requested = None if row["requested_at"] is None else number_value(
        row["requested_at"], minimum=baseline, maximum=elapsed,
        context="communicated food request",
    )
    parameters = MOODLET_CATALOG.definitions[MoodletId.FOOD_MONOTONY].parameters
    assert isinstance(parameters, FoodMonotonyParameters)
    ignored = integer_value(row["ignored_portions"], minimum=0,
                            maximum=parameters.free_ignored_portions + 1,
                            context="ignored food requests")
    if (food is None and (intakes or requested is not None or row["request_pending"])
            or food is not None and not intakes
            or row["request_pending"] and requested is not None
            or ignored and requested is None):
        raise ValueError("Inconsistent food repetition evidence")
    return FoodRepetitionMemory(food, intakes, row["request_pending"],
                                requested, ignored)
