"""Concrete immediate causes and one care-pattern fact per upsetting incident."""

from typing import Mapping

from .care_evidence import CareActivity, CareExperience
from .care_experiences import allocate_experience_receipt, record_experience
from .moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletDefinition,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    reinforce_moodlet,
)
from .wishes import WishArea, WishTargetKind


def record_upsetting_interaction(
    state: MoodletState,
    family: MoodletId,
    *,
    elapsed: float,
    attribution: MoodletAttribution,
    definitions: Mapping[MoodletId, MoodletDefinition],
    incident_id: str | None = None,
    target_id: str | None = None,
    object_id: str | None = None,
    boundary_violated: bool = False,
) -> MoodletState:
    """Escalations retain real causes but do not manufacture independent incidents."""
    state, receipt = allocate_experience_receipt(
        state, elapsed=elapsed, prefix=family.value,
    )
    food = family == MoodletId.FOOD_MONOTONY
    state = reinforce_moodlet(
        state,
        family,
        elapsed=elapsed,
        definitions=definitions,
        attribution=attribution,
        cause=MoodletCause(
            MoodletCauseKind.INTERACTION,
            elapsed,
            receipt,
            attribution,
            target_id=target_id or family.value,
            outcome=MoodletOutcome.INTAKE if food else MoodletOutcome.COMPLETED,
            object_id=object_id,
        ),
    )
    if attribution != MoodletAttribution.USER:
        return state
    activity = {
        MoodletId.POKING: CareActivity.POKING,
        MoodletId.CROWDED: CareActivity.PETTING,
        MoodletId.WITHHELD: CareActivity.WITHHOLDING,
        MoodletId.DISRUPTED: CareActivity.ARRANGEMENT,
        MoodletId.FOOD_MONOTONY: CareActivity.FOOD_HANDOVER,
    }[family]
    area = (
        WishArea.FOOD
        if food
        else WishArea.AFFECTION
        if family == MoodletId.CROWDED
        else None
    )
    kind = (
        WishTargetKind.FOOD
        if food
        else WishTargetKind.CARE
        if family == MoodletId.CROWDED
        else None
    )
    target = target_id if food else "pet" if family == MoodletId.CROWDED else None
    state, _ = record_experience(
        state,
        CareExperience(
            f"incident:{family}:{incident_id}" if incident_id is not None else receipt,
            elapsed,
            activity,
            MoodletOutcome.INTAKE if food else MoodletOutcome.COMPLETED,
            area,
            kind,
            target,
            upsetting=True,
            boundary_violated=boundary_violated,
            object_id=object_id,
        ),
    )
    return state
