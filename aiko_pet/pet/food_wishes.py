"""Personal food-transfer snapshots and permissions, without World inference."""

from dataclasses import dataclass, replace
from typing import Mapping

from .food_handover import (
    MAX_FOOD_HANDOVERS,
    FoodHandoverReceipt,
    FoodWishSnapshot,
    HandoverStatus,
)
from .moodlets import MoodletOutcome
from .wish_fulfillment import wish_cause
from .wish_matching import assign_activity_wish, wish_assignment_priority
from .wishes import (
    ActiveWish,
    WishArea,
    WishDefinition,
    WishId,
    WishResolution,
    WishState,
    WishTargetMode,
    wish_refresh_deadline,
)


def begin_food_handover(
    state: WishState,
    *,
    handover_id: str,
    object_id: str,
    elapsed: float,
    definitions: Mapping[WishId, WishDefinition],
) -> WishState:
    """Capture only wishes present at the confirmed actual transfer boundary."""
    previous = next(
        (r for r in state.food_handovers if r.handover_id == handover_id), None
    )
    if previous is not None:
        if previous.object_id != object_id:
            raise ValueError("Conflicting actual handover identity")
        return state
    receipts = [r for r in state.food_handovers if r.object_id != object_id]
    if len(receipts) >= MAX_FOOD_HANDOVERS:
        retired = next(
            (r for r in receipts if r.status != HandoverStatus.PENDING), None
        )
        if retired is None:
            raise ValueError("Too many unresolved personal handovers")
        receipts.remove(retired)
    context = tuple(
        FoodWishSnapshot(
            w.instance_id,
            w.definition_id,
            w.target or definitions[w.definition_id].bind_target(w.target_id),
            w.goal_snapshot,
            w.created_at,
            w.expressed_at,
            w.pinned,
        )
        for w in state.active
        if w.is_active_at(elapsed)
        and definitions[w.definition_id].area == WishArea.FOOD
    )
    receipts.append(FoodHandoverReceipt(handover_id, object_id, elapsed, context))
    return replace(state, food_handovers=tuple(receipts))


def account_food_wish(state: WishState, instance_id: int) -> WishState:
    """A settled identity cannot be awarded by another still pending handover."""
    return replace(
        state,
        food_handovers=tuple(
            replace(r, accounted_wish_ids=(*r.accounted_wish_ids, instance_id))
            if instance_id not in r.accounted_wish_ids
            and any(w.instance_id == instance_id for w in r.wishes)
            else r
            for r in state.food_handovers
        ),
    )


def recognize_food_handover(
    state: WishState,
    *,
    handover_id: str,
    food_id: str,
    elapsed: float,
    definitions: Mapping[WishId, WishDefinition],
) -> WishResolution:
    receipt = next(
        (r for r in state.food_handovers if r.handover_id == handover_id), None
    )
    if (
        receipt is None
        or receipt.status != HandoverStatus.PENDING
        or elapsed < receipt.handed_over_at
    ):
        return WishResolution(state)
    if not any(
        food_id in d.targets for d in definitions.values() if d.area == WishArea.FOOD
    ):
        raise ValueError("Unknown recognized food")
    candidates = tuple(
        w for w in receipt.wishes if w.instance_id not in receipt.accounted_wish_ids
    )
    negative = tuple(
        w
        for w in candidates
        if w.target.mode == WishTargetMode.EXCLUDE and w.target.target_id == food_id
    )
    positive = tuple(
        w
        for w in candidates
        if food_id in definitions[w.definition_id].targets
        and w.target.matches(definitions[w.definition_id].target_kind, food_id)
    )
    selected = min(negative or positive, key=wish_assignment_priority, default=None)
    evaluated = replace(
        receipt,
        recognized_food_id=food_id,
        recognized_at=elapsed,
        status=HandoverStatus.EVALUATED,
        resolved_wish_instance_id=selected.instance_id if selected else None,
    )
    state = replace(
        state,
        food_handovers=tuple(
            evaluated if r.handover_id == handover_id else r
            for r in state.food_handovers
        ),
    )
    if selected is None:
        return WishResolution(state)
    state = account_food_wish(state, selected.instance_id)
    state = replace(
        state,
        active=tuple(w for w in state.active if w.instance_id != selected.instance_id),
        refresh_at=wish_refresh_deadline(state, elapsed),
    )
    original = ActiveWish(
        selected.instance_id,
        selected.definition_id,
        selected.target.target_id or "",
        selected.created_at,
        elapsed + 1,
        goal=selected.goal,
        target=selected.target,
    )
    cause = replace(
        wish_cause(
            original,
            elapsed=elapsed,
            event_id=receipt.handover_id,
            outcome=MoodletOutcome.HANDOVER,
            target_id=food_id,
            object_id=receipt.object_id,
            failed=bool(negative),
        ),
        handed_over_at=receipt.handed_over_at,
    )
    return WishResolution(
        state, None if negative else definitions[selected.definition_id], cause
    )


def withdraw_food_handovers(state: WishState, object_ids: frozenset[str]) -> WishState:
    """Actual user withdrawal/removal cancels open context and releases permissions."""
    return replace(
        state,
        food_handovers=tuple(
            replace(r, status=HandoverStatus.CANCELLED)
            if r.object_id in object_ids and r.status == HandoverStatus.PENDING
            else r
            for r in state.food_handovers
            if r.object_id not in object_ids or r.status == HandoverStatus.PENDING
        ),
    )


@dataclass(frozen=True, slots=True)
class FoodWishPermission:
    wish_instance_id: int | None = None
    requested: bool = False
    excluded: bool = False


def food_wish_permission(
    state: WishState,
    food_id: str,
    *,
    elapsed: float,
    definitions: Mapping[WishId, WishDefinition],
    object_id: str | None = None,
    personal: bool = True,
) -> FoodWishPermission:
    receipt = next(
        (
            r
            for r in reversed(state.food_handovers)
            if r.object_id == object_id
            and r.status == HandoverStatus.EVALUATED
            and r.recognized_food_id == food_id
        ),
        None,
    )
    if receipt is not None:
        selected = next(
            (
                w
                for w in receipt.wishes
                if w.instance_id == receipt.resolved_wish_instance_id
            ),
            None,
        )
        return FoodWishPermission(
            requested=selected is not None
            and selected.target.mode == WishTargetMode.EXACT,
            excluded=selected is not None
            and selected.target.mode == WishTargetMode.EXCLUDE
            and selected.target.target_id == food_id,
        )
    if personal and any(
        w.is_active_at(elapsed) and w.definition_id == WishId.AVOID_FOOD
        and (w.target.target_id if w.target else w.target_id) == food_id
        for w in state.active
    ):
        return FoodWishPermission(excluded=True)
    wish = assign_activity_wish(
        state, WishArea.FOOD, food_id, elapsed=elapsed, definitions=definitions
    )
    return FoodWishPermission(
        wish.instance_id if wish else None, requested=personal and wish is not None
    )
