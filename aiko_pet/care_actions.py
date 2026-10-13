"""Legacy care-policy imports; canonical behavior is in pet.care_actions."""

from __future__ import annotations

from .pet.care_actions import (
    CareValues as CareValues,
    CareState as CareState,
    CareTransition as CareTransition,
    plan_care_action as plan_care_action,
    apply_care_action as apply_care_action,
    resolve_care_time as resolve_care_time,
)
