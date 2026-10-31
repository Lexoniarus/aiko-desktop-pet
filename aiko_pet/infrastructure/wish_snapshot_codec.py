"""Shared original goal/target validation for active wishes and cause snapshots."""

from typing import Any

from ..pet.catalog_validation import enum_value, integer_value, object_fields
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import (
    WishArea,
    WishGoal,
    WishId,
    WishObjective,
    WishTarget,
    WishTargetKind,
    WishTargetMode,
    legacy_wish_goal,
)


def decode_wish_goal(raw: Any, key: WishId) -> WishGoal:
    """Validate an explicit original goal, including preserved pre-migration forms."""
    row = object_fields(raw, ("objective", "required_count"), context="wish goal")
    goal = WishGoal(
        enum_value(row["objective"], WishObjective, context="wish goal objective"),
        integer_value(
            row["required_count"], minimum=0, maximum=100, context="wish goal count"
        ),
    )
    allowed: tuple[WishGoal, ...] = (WISH_CATALOG.definitions[key].goal,)
    try:
        allowed += (legacy_wish_goal(key),)
    except ValueError:
        # Newly introduced forms have no historical goal to fabricate.
        pass
    if (
        goal.objective not in {g.objective for g in allowed}
        or (WISH_CATALOG.definitions[key].area == WishArea.GAMES)
        != (goal.required_count > 0)
        or key
        in (
            WishId.WIN_ROUND,
            WishId.AVOID_ROUND_LOSS,
            WishId.REMATCH_GAME,
            WishId.COMEBACK_GAME,
        )
        and goal.required_count != 1
    ):
        raise ValueError("Incompatible saved wish objective/count")
    return goal


def encode_wish_goal(goal: WishGoal) -> dict[str, Any]:
    return dict(objective=goal.objective.value, required_count=goal.required_count)


def decode_wish_target(raw: Any, key: WishId) -> WishTarget:
    row = object_fields(raw, ("kind", "mode", "target_id"), context="wish target")
    target = WishTarget(
        enum_value(row["kind"], WishTargetKind, context="wish target kind"),
        enum_value(row["mode"], WishTargetMode, context="wish target mode"),
        row["target_id"],
    )
    definition = WISH_CATALOG.definitions[key]
    if (
        target.kind != definition.target_kind
        or target.mode != definition.target_mode
        or target.target_id is not None
        and target.target_id not in definition.targets
    ):
        raise ValueError("Incompatible original wish target")
    return target


def encode_wish_target(target: WishTarget) -> dict[str, Any]:
    return dict(
        kind=target.kind.value, mode=target.mode.value, target_id=target.target_id
    )
