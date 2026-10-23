"""Awake wish selection on Pet's shared elapsed axis; no UI or offline engine."""

import random
from dataclasses import replace
from typing import Mapping

from .balance import BALANCE
from .needs import NeedLevels
from .wishes import (
    ActiveWish,
    WishArea,
    WishContext,
    WishDefinition,
    WishId,
    WishState,
    WishTargetMode,
    expire_wishes,
)


def _candidate_targets(
    definition: WishDefinition, *, needs: NeedLevels, context: WishContext,
) -> tuple[str, ...]:
    """Current suitability never extends or replaces an existing objective."""
    # The current picker binds one concrete game/category. Flexible references
    # and real experience assignment are introduced by the lifecycle slice.
    if definition.experience is not None or (
        definition.area in (WishArea.GAMES, WishArea.SOCIAL)
        and definition.target_mode != WishTargetMode.EXACT
    ):
        return ()
    threshold = BALANCE.number("wishes", "creation_need_threshold")
    if (definition.selection_weight == 0
            or definition.area == WishArea.FOOD and needs.satiety > threshold
            or definition.area == WishArea.AFFECTION
            and (needs.affection > threshold or context.crowded
                 or not context.petting_welcome)
            or definition.id in (WishId.SINGLE, WishId.TWO_PARTS, WishId.FACT)
            and not context.online_social):
        return ()
    if definition.id == WishId.AVOID_FOOD:
        return tuple(t for t in definition.targets if t == context.repetitive_food)
    if definition.area == WishArea.FOOD:
        return tuple(t for t in definition.targets if t != context.repetitive_food)
    return definition.targets


def replenish_wishes(
    state: WishState, *, elapsed: float, sleeping: bool, needs: NeedLevels,
    context: WishContext, definitions: Mapping[WishId, WishDefinition],
    rng: random.Random,
) -> WishState:
    """Refresh once when awake and due, never replay missed offline rotations."""
    state = expire_wishes(state, elapsed=elapsed)
    if sleeping or state.refresh_at is not None and elapsed < state.refresh_at:
        return state
    deadline = elapsed + BALANCE.integer("wishes", "refresh_interval_seconds")
    # Existing saved game goals retain their original deadline and progress.
    # Other old four-hour desires join the common schedule at this live boundary.
    active = [replace(w, expires_at=min(w.expires_at, deadline))
              if not w.pinned and w.target is None
              and definitions[w.definition_id].area != WishArea.GAMES else w
              for w in state.active]
    occupied = {definitions[w.definition_id].area for w in active}
    anchors = dict(state.last_created_by_area)
    candidates: dict[WishArea, list[tuple[WishDefinition, tuple[str, ...]]]] = {}
    for definition in definitions.values():
        if definition.area in occupied:
            continue
        targets = _candidate_targets(definition, needs=needs, context=context)
        if targets:
            candidates.setdefault(definition.area, []).append((definition, targets))
    next_id = state.next_instance_id
    while candidates and len(active) < BALANCE.integer("wishes", "maximum_active"):
        area = rng.choice(tuple(candidates))
        forms = candidates.pop(area)
        definition, targets = rng.choices(
            forms, weights=[d.selection_weight for d, _targets in forms], k=1,
        )[0]
        if next_id >= 2**63 - 1:
            raise ValueError("Wish instance allocation exhausted")
        target = definition.bind_target(rng.choice(targets))
        active.append(ActiveWish(
            next_id, definition.id, target.target_id or "", elapsed, deadline,
            goal=definition.goal, target=target,
        ))
        next_id += 1
        anchors[area] = elapsed
    return replace(
        state, next_instance_id=next_id, active=tuple(active), refresh_at=deadline,
        last_created_by_area=tuple((a, anchors[a]) for a in WishArea if a in anchors),
    )
