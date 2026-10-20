"""Strict, read-only Moodlet catalogue; no episode or transition execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Collection, Literal, Mapping

from .catalog_validation import (
    enum_value,
    integer_value,
    load_json,
    number_value,
    object_fields,
)
from .content import GERMAN_TEXT
from .moodlets import (
    EmotionalDirection,
    FoodMonotonyParameters,
    MoodletDecay,
    MoodletDefinition,
    MoodletGroup,
    MoodletId,
    MoodletParameters,
    MoodletPolarity,
    PettingParameters,
    PettingTolerance,
    PokingParameters,
    PoorCareParameters,
    RelocationParameters,
    WithholdingParameters,
)


@dataclass(frozen=True, slots=True)
class MoodletCatalog:
    definitions: Mapping[MoodletId, MoodletDefinition]


def _seconds(raw: Any, context: str, *, minimum: int = 1) -> int:
    return integer_value(raw, minimum=minimum, maximum=604800, context=context)


def _loss(raw: dict[str, Any], context: str) -> tuple[float, float, int]:
    amount = number_value(raw["friendship_loss_points"], minimum=0, maximum=100,
                          context=f"{context}.friendship_loss_points")
    cap = number_value(raw["friendship_loss_cap_points"], minimum=amount,
                       maximum=100, context=f"{context}.friendship_loss_cap_points")
    window = _seconds(raw["friendship_loss_window_seconds"],
                      f"{context}.friendship_loss_window_seconds")
    return amount, cap, window


_LOSS_FIELDS = (
    "friendship_loss_points", "friendship_loss_cap_points",
    "friendship_loss_window_seconds",
)


def _parameters(key: MoodletId, value: Any) -> MoodletParameters:
    context = f"moodlets.{key}.parameters"
    if key == MoodletId.POKING:
        row = object_fields(value, ("escalation_pokes",), context=context)
        return PokingParameters(integer_value(
            row["escalation_pokes"], minimum=1, maximum=100, context=context,
        ))
    if key == MoodletId.CROWDED:
        row = object_fields(value, (
            "escalation_attempts", "boundary_window_seconds", "refusal_seconds",
            "tolerances", *_LOSS_FIELDS,
        ), context=context)
        refusal = row["refusal_seconds"]
        if not isinstance(refusal, list) or len(refusal) != 3:
            raise ValueError(f"{context}: expected three refusal durations")
        deadlines = tuple(_seconds(v, context) for v in refusal)
        if any(a > b for a, b in zip(deadlines, deadlines[1:])):
            raise ValueError(f"{context}: refusal durations must not decrease")
        rows = row["tolerances"]
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{context}: missing friendship tolerances")
        tolerances: list[PettingTolerance] = []
        for raw in rows:
            entry = object_fields(raw, (
                "maximum_friendship_level", "affection_threshold",
            ), context=context)
            tolerances.append(PettingTolerance(
                integer_value(entry["maximum_friendship_level"], minimum=1,
                              maximum=10, context=context),
                number_value(entry["affection_threshold"], minimum=0,
                             maximum=100, context=context),
            ))
        if tolerances[-1].maximum_friendship_level != 10 or any(
            a.maximum_friendship_level >= b.maximum_friendship_level
            or a.affection_threshold > b.affection_threshold
            for a, b in zip(tolerances, tolerances[1:])
        ):
            raise ValueError(f"{context}: invalid friendship tolerance ordering")
        return PettingParameters(
            integer_value(row["escalation_attempts"], minimum=1, maximum=100,
                          context=context),
            _seconds(row["boundary_window_seconds"], context), deadlines,
            tuple(tolerances), *_loss(row, context),
        )
    if key == MoodletId.FOOD_MONOTONY:
        row = object_fields(value, (
            "sequence_window_seconds", "request_lifetime_seconds",
            "free_ignored_portions", *_LOSS_FIELDS,
        ), context=context)
        return FoodMonotonyParameters(
            _seconds(row["sequence_window_seconds"], context),
            _seconds(row["request_lifetime_seconds"], context),
            integer_value(row["free_ignored_portions"], minimum=0, maximum=100,
                          context=context), *_loss(row, context),
        )
    if key == MoodletId.WITHHELD:
        row = object_fields(value, ("escalation_seconds",), context=context)
        return WithholdingParameters(_seconds(row["escalation_seconds"], context))
    if key == MoodletId.DISRUPTED:
        row = object_fields(value, _LOSS_FIELDS, context=context)
        return RelocationParameters(*_loss(row, context))
    poor_care: dict[
        MoodletId, Literal["satiety", "energy", "fun", "social", "affection"],
    ] = {
        MoodletId.HUNGER_WORN: "satiety", MoodletId.EXHAUSTION_IRRITATED: "energy",
        MoodletId.UNSTIMULATED: "fun", MoodletId.LONELY: "social",
        MoodletId.MISSING_CLOSENESS: "affection",
    }
    if key in poor_care:
        row = object_fields(value, ("need",), context=context)
        if row["need"] != poor_care[key]:
            raise ValueError(f"{context}: incorrect source need")
        return PoorCareParameters(poor_care[key])
    if value is not None:
        raise ValueError(f"{context}: wish fulfillment has no trigger parameters")
    return None


def parse_moodlet_catalog(
    raw: Any, *, text_keys: Collection[str] = GERMAN_TEXT.messages,
) -> MoodletCatalog:
    data = object_fields(raw, ("version", "moodlets"), context="moodlets")
    if type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("Unsupported Moodlet catalogue version")
    rows = data["moodlets"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("Moodlet catalogue must contain definitions")
    definitions: dict[MoodletId, MoodletDefinition] = {}
    for value in rows:
        row = object_fields(value, (
            "id", "polarity", "direction", "group", "level_points", "decay",
            "decay_stage_seconds", "relief_seconds", "parameters",
        ), context="moodlet")
        key = enum_value(row["id"], MoodletId, context="moodlet.id")
        if key in definitions:
            raise ValueError(f"Duplicate Moodlet ID: {key}")
        polarity = enum_value(row["polarity"], MoodletPolarity, context=str(key))
        direction = enum_value(row["direction"], EmotionalDirection, context=str(key))
        group = enum_value(row["group"], MoodletGroup, context=str(key))
        decay = enum_value(row["decay"], MoodletDecay, context=str(key))
        points = row["level_points"]
        levels = 1 if key == MoodletId.FOOD_FULFILLED else 3
        if not isinstance(points, list) or len(points) != levels:
            raise ValueError(f"{key}: expected {levels} level contributions")
        values = tuple(integer_value(p, minimum=-100, maximum=100,
                                     context=f"{key}.level_points") for p in points)
        sign = 1 if polarity == MoodletPolarity.POSITIVE else -1
        if any(p * sign <= 0 for p in values) or any(
            abs(a) >= abs(b) for a, b in zip(values, values[1:])
        ):
            raise ValueError(f"{key}: contributions must match polarity and grow")
        positive_direction = direction in (
            EmotionalDirection.CHEERFUL, EmotionalDirection.PROUD,
            EmotionalDirection.RELIEVED, EmotionalDirection.AFFECTIONATE,
        )
        positive_group = group not in (
            MoodletGroup.INTERACTION, MoodletGroup.POOR_CARE,
        )
        parameters = _parameters(key, row["parameters"])
        positive = polarity == MoodletPolarity.POSITIVE
        if (positive != positive_direction or positive != positive_group
                or positive != (parameters is None)
                or (group == MoodletGroup.POOR_CARE)
                != isinstance(parameters, PoorCareParameters)):
            raise ValueError(f"{key}: inconsistent polarity, direction or group")
        expected_decay = (
            MoodletDecay.STABLE_RECOVERY if group == MoodletGroup.POOR_CARE
            else MoodletDecay.RESOLVED_QUIET_TIME if key == MoodletId.WITHHELD
            else MoodletDecay.QUIET_TIME
        )
        if decay != expected_decay:
            raise ValueError(f"{key}: incorrect decay prerequisite")
        definition = MoodletDefinition(
            key, polarity, direction, group, values, decay,
            _seconds(row["decay_stage_seconds"], str(key)),
            _seconds(row["relief_seconds"], str(key), minimum=0), parameters,
        )
        if positive and definition.relief_seconds:
            raise ValueError(f"{key}: positive impressions cannot receive relief")
        if not {definition.label_key, definition.description_key} <= set(text_keys):
            raise ValueError(f"{key}: missing localized label or description")
        definitions[key] = definition
    if set(definitions) != set(MoodletId):
        raise ValueError("Moodlet catalogue must define every supported family")
    return MoodletCatalog(MappingProxyType(definitions))


def load_packaged_moodlet_catalog(
    path: Path = Path(__file__).resolve().parents[1] / "data/moodlets.json",
) -> MoodletCatalog:
    return parse_moodlet_catalog(load_json(path))


MOODLET_CATALOG = load_packaged_moodlet_catalog()
