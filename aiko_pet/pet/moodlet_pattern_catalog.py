"""Decode immutable care-pattern prerequisites; never evaluate personal evidence."""

from dataclasses import fields
from types import MappingProxyType
from typing import Any, Mapping

from .balance import BALANCE
from .catalog_validation import integer_value, number_value, object_fields
from .moodlet_patterns import (
    AppreciationParameters,
    GuardedParameters,
    LongTermMoodletPolicy,
    LongTermPatternParameters,
    OptimismParameters,
    OverlookedParameters,
    TrustParameters,
    UncertaintyParameters,
)
from .moodlets import MoodletId

PATTERN_TYPES: Mapping[MoodletId, type[LongTermPatternParameters]] = MappingProxyType({
    MoodletId.TRUSTING: TrustParameters,
    MoodletId.APPRECIATED: AppreciationParameters,
    MoodletId.OPTIMISTIC: OptimismParameters,
    MoodletId.UNCERTAIN: UncertaintyParameters,
    MoodletId.OVERLOOKED: OverlookedParameters,
    MoodletId.GUARDED: GuardedParameters,
})


def parse_long_term_policy(raw: Any) -> LongTermMoodletPolicy:
    context = "moodlets.long_term_policy"
    row = object_fields(raw, (
        "period_seconds", "positive_mood_cap_points", "negative_mood_cap_points",
        "positive_friendship_rate", "negative_friendship_rate",
    ), context=context)
    return LongTermMoodletPolicy(
        integer_value(row["period_seconds"], minimum=86400, maximum=86400,
                      context=f"{context}.period_seconds"),
        number_value(row["positive_mood_cap_points"], minimum=0.001,
                     maximum=BALANCE.number("moodlets", "positive_cap_points"),
                     context=f"{context}.positive_mood_cap_points"),
        number_value(row["negative_mood_cap_points"], minimum=0.001,
                     maximum=BALANCE.number("moodlets", "negative_cap_points"),
                     context=f"{context}.negative_mood_cap_points"),
        number_value(row["positive_friendship_rate"], minimum=0.000001,
                     maximum=BALANCE.number("friendship", "positive_moodlet_rate"),
                     context=f"{context}.positive_friendship_rate"),
        number_value(row["negative_friendship_rate"], minimum=0.000001,
                     maximum=BALANCE.number("friendship", "negative_moodlet_rate"),
                     context=f"{context}.negative_friendship_rate"),
    )


def parse_pattern_parameters(
    key: MoodletId, raw: Any, policy: LongTermMoodletPolicy,
) -> LongTermPatternParameters:
    context = f"moodlets.{key}.parameters"
    kind = PATTERN_TYPES[key]
    row = object_fields(raw, tuple(field.name for field in fields(kind)),
                        context=context)

    def count(name: str, minimum: int = 1, maximum: int = 100) -> int:
        return integer_value(row[name], minimum=minimum, maximum=maximum,
                             context=f"{context}.{name}")

    def seconds(name: str) -> int:
        return count(name, maximum=policy.period_seconds)

    def distributed(encounters: int) -> int:
        gap = seconds("minimum_encounter_gap_seconds")
        if (encounters - 1) * gap > policy.period_seconds:
            raise ValueError(f"{context}: encounters cannot fit qualification period")
        return gap

    if key == MoodletId.TRUSTING:
        encounters = count("minimum_encounters", 3)
        gap = distributed(encounters)
        span = seconds("minimum_encounter_span_seconds")
        if span < (encounters - 1) * gap:
            raise ValueError(f"{context}: span cannot contain distributed encounters")
        return TrustParameters(
            encounters, gap, span, count("minimum_activity_kinds", 2, 4),
            count("care_exposure_level_limit", 1, 1),
            count("maximum_boundary_violations", 0, 0),
        )
    if key == MoodletId.APPRECIATED:
        wishes = count("minimum_fulfilled_wishes", 3)
        encounters = count("minimum_encounters", 2, wishes)
        return AppreciationParameters(
            wishes, count("minimum_wish_areas", 2, min(4, wishes)),
            encounters, distributed(encounters),
            count("maximum_boundary_violations", 0, 0),
        )
    if key == MoodletId.OPTIMISTIC:
        activities = count("minimum_pleasant_activities", 3)
        encounters = count("minimum_encounters", 2, activities)
        return OptimismParameters(
            activities, count("minimum_activity_areas", 2, min(4, activities)),
            encounters, distributed(encounters), count("minimum_successes"),
            count("maximum_kind_per_encounter", 1, 1),
        )
    if key == MoodletId.UNCERTAIN:
        pairs = count("minimum_pairs", 2)
        gap = seconds("minimum_incident_gap_seconds")
        if (pairs - 1) * gap > policy.period_seconds:
            raise ValueError(f"{context}: incident pairs cannot fit period")
        return UncertaintyParameters(pairs, gap)
    if key == MoodletId.OVERLOOKED:
        return OverlookedParameters(
            count("maximum_encounters", 0, 1), seconds("awake_contact_gap_seconds"),
        )
    return GuardedParameters(
        count("minimum_incidents", 3), seconds("minimum_incident_span_seconds"),
    )
