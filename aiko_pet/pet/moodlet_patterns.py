"""Immutable longer-term qualification data, without evidence or evaluation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LongTermMoodletPolicy:
    """Shared period/caps and per-intensity rates per existing thirty-second tick."""

    period_seconds: int
    positive_mood_cap_points: float
    negative_mood_cap_points: float
    positive_friendship_rate: float
    negative_friendship_rate: float


@dataclass(frozen=True, slots=True)
class LongTermPatternParameters:
    """Marker for bounded pattern prerequisites; not a qualified care period."""


@dataclass(frozen=True, slots=True)
class TrustParameters(LongTermPatternParameters):
    minimum_encounters: int
    minimum_encounter_gap_seconds: int
    minimum_encounter_span_seconds: int
    minimum_activity_kinds: int
    care_exposure_level_limit: int
    maximum_boundary_violations: int


@dataclass(frozen=True, slots=True)
class AppreciationParameters(LongTermPatternParameters):
    minimum_fulfilled_wishes: int
    minimum_wish_areas: int
    minimum_encounters: int
    minimum_encounter_gap_seconds: int
    maximum_boundary_violations: int


@dataclass(frozen=True, slots=True)
class OptimismParameters(LongTermPatternParameters):
    minimum_pleasant_activities: int
    minimum_activity_areas: int
    minimum_encounters: int
    minimum_encounter_gap_seconds: int
    minimum_successes: int
    maximum_kind_per_encounter: int


@dataclass(frozen=True, slots=True)
class UncertaintyParameters(LongTermPatternParameters):
    """Each independent pair is a pleasant encounter followed by bad treatment."""

    minimum_pairs: int
    minimum_incident_gap_seconds: int


@dataclass(frozen=True, slots=True)
class OverlookedParameters(LongTermPatternParameters):
    maximum_encounters: int
    awake_contact_gap_seconds: int


@dataclass(frozen=True, slots=True)
class GuardedParameters(LongTermPatternParameters):
    minimum_incidents: int
    minimum_incident_span_seconds: int
