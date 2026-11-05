"""Shared deterministic assignment of one original wish before an outcome."""

from typing import Mapping

from .food_handover import FoodWishSnapshot
from .wishes import (
    ActiveWish,
    WishArea,
    WishDefinition,
    WishId,
    WishObjective,
    WishState,
    WishTargetMode,
)


def wish_matches_activity(
    wish: ActiveWish, area: WishArea, target_id: str, *,
    definitions: Mapping[WishId, WishDefinition],
) -> bool:
    """Match supported actual targets against the saved exact/any/exclude meaning."""
    definition = definitions[wish.definition_id]
    if definition.area != area or target_id not in definition.targets:
        return False
    return (wish.target.matches(definition.target_kind, target_id)
            if wish.target is not None else wish.target_id == target_id)


def assign_activity_wish(
    state: WishState, area: WishArea, target_id: str, *, elapsed: float,
    definitions: Mapping[WishId, WishDefinition],
) -> ActiveWish | None:
    """Pin, target specificity, existing progress, then age and stable identity.

    No preference depends on the future result or a family label. Equally
    concrete goals use saved progress/age rather than an invented win-first rule.
    Handover-specific food treatment belongs to its separate admission boundary.
    """
    return min((w for w in state.active
                if w.is_active_at(elapsed)
                and w.goal_snapshot.objective != WishObjective.FOOD_HANDOVER
                and wish_matches_activity(w, area, target_id, definitions=definitions)),
               key=wish_assignment_priority, default=None)


def wish_assignment_priority(
    wish: ActiveWish | FoodWishSnapshot,
) -> tuple[bool, int, bool, float, int]:
    mode = wish.target.mode if wish.target is not None else WishTargetMode.EXACT
    specificity = {WishTargetMode.EXACT: 0, WishTargetMode.EXCLUDE: 1,
                   WishTargetMode.ANY: 2}[mode]
    progressed = isinstance(wish, ActiveWish) and bool(wish.game.completed_rounds)
    return (not wish.pinned, specificity, not progressed,
            wish.created_at, wish.instance_id)
