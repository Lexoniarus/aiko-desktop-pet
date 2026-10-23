"""Bounded personal experience values, owned through Pet's existing Moodlet state.

No values infer events, group visits, qualify care periods or duplicate need
exposure buckets. Actual game/social facts support eligibility and completion.
Encounter
qualification and period evaluation belong to subsequent slices.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .moodlets import MoodletId, MoodletOutcome
    from .wishes import WishArea, WishTargetKind

MAX_CARE_ENCOUNTERS = 128
MAX_CARE_EXPERIENCES = 512


class CareActivity(StrEnum):
    PLAY = "play"
    SOCIAL = "social"
    PETTING = "petting"
    FOOD_HANDOVER = "food_handover"
    POKING = "poking"
    WITHHOLDING = "withholding"
    ARRANGEMENT = "arrangement"


@dataclass(frozen=True, slots=True)
class CareEncounter:
    instance_id: int
    started_at: float
    last_activity_at: float


@dataclass(frozen=True, slots=True)
class CareExperience:
    receipt_id: str
    occurred_at: float
    activity: CareActivity
    outcome: MoodletOutcome
    area: WishArea | None = None
    target_kind: WishTargetKind | None = None
    target_id: str | None = None
    encounter_id: int | None = None
    wish_instance_id: int | None = None
    pleasant: bool = False
    upsetting: bool = False
    boundary_violated: bool = False
    object_id: str | None = None


@dataclass(frozen=True, slots=True)
class LongTermProgress:
    definition_id: MoodletId
    period_start: float
    processed_until: float
    last_accounted_at: float
    awake_contact_gap_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class CareEvidenceState:
    baseline: float
    next_encounter_id: int = 1
    encounters: tuple[CareEncounter, ...] = ()
    experiences: tuple[CareExperience, ...] = ()
    progress: tuple[LongTermProgress, ...] = ()


@dataclass(frozen=True, slots=True)
class CarePeriodSummary:
    """Actual bounded period facts retained by a cause after raw evidence expires."""

    started_at: float
    ended_at: float
    encounters: int = 0
    activity_kinds: tuple[CareActivity, ...] = ()
    fulfilled_wishes: int = 0
    wish_areas: tuple[WishArea, ...] = ()
    successes: int = 0
    upsetting_incidents: int = 0
    boundary_violations: int = 0
    uncertainty_pairs: int = 0
    awake_contact_gap_seconds: float = 0.0
    care_exposure_level: int = 0
