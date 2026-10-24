"""Awake wish selection on Pet's shared elapsed axis; no UI or offline engine."""

import random
from dataclasses import dataclass, replace
from typing import Mapping

from .balance import BALANCE
from .care_evidence import CareActivity
from .moodlets import MoodletOutcome
from .needs import NeedLevels
from .wishes import (
    ActiveWish,
    WishArea,
    WishContext,
    WishDefinition,
    WishExperienceKind,
    WishId,
    WishState,
    WishTarget,
    WishTargetKind,
    WishTargetMode,
    expire_wishes,
)


def wish_area_weight(area: WishArea, needs: NeedLevels) -> int:
    """A high need bar lowers desire frequency without excluding its area."""
    value = {WishArea.FOOD: needs.satiety, WishArea.GAMES: needs.fun,
             WishArea.SOCIAL: needs.social, WishArea.AFFECTION: needs.affection}[area]
    for threshold, band in (("high", "satisfied"), ("medium", "moderate"),
                            ("low", "low")):
        if value > BALANCE.number("wishes", f"need_{threshold}_threshold"):
            return BALANCE.integer("wishes", f"area_weight_{band}")
    return BALANCE.integer("wishes", "area_weight_critical")


@dataclass(frozen=True, slots=True)
class _Candidate:
    definition: WishDefinition
    targets: tuple[WishTarget, ...]
    weight: float


def _candidate(
    definition: WishDefinition, *, elapsed: float, context: WishContext,
    active: list[ActiveWish], definitions: Mapping[WishId, WishDefinition],
) -> _Candidate | None:
    """Actual capabilities and evidence gate creation, independently of speech."""
    if (definition.selection_weight == 0
            or definition.area == WishArea.AFFECTION
            and (context.crowded or context.petting_refused)
            or definition.id in (WishId.SINGLE, WishId.TWO_PARTS, WishId.FACT)
            and not context.online_social):
        return None
    references: tuple[str | None, ...] = definition.targets
    weight = float(definition.selection_weight)
    if definition.experience is not None:
        evidence = context.recent_play
        requirement = definition.experience
        if (evidence is None or evidence.activity != CareActivity.PLAY
                or evidence.target_kind != WishTargetKind.GAME
                or evidence.outcome not in (MoodletOutcome.WIN, MoodletOutcome.LOSS,
                                            MoodletOutcome.DRAW)
                or not 0 <= elapsed - evidence.occurred_at < requirement.window_seconds
                or evidence.target_id not in definition.targets
                or requirement.kind == WishExperienceKind.LAST_ROUND_LOSS
                and evidence.outcome != MoodletOutcome.LOSS):
            return None
        references = (evidence.target_id,)
        weight *= requirement.weight_multiplier
        # Revanche variants for this reference are alternatives, never two slots.
        if definition.id in (WishId.REMATCH_GAME, WishId.COMEBACK_GAME) and any(
            w.definition_id in (WishId.REMATCH_GAME, WishId.COMEBACK_GAME)
            and w.target_id == evidence.target_id for w in active
        ):
            return None
    elif definition.id == WishId.AVOID_FOOD:
        references = tuple(t for t in definition.targets
                           if t == context.repetitive_food)
    elif definition.target_mode == WishTargetMode.ANY:
        references = (None,)
    elif definition.area == WishArea.FOOD:
        references = tuple(t for t in definition.targets
                           if t != context.repetitive_food)
    occupied = {
        (w.goal_snapshot, w.target or WishTarget(
            definitions[w.definition_id].target_kind,
            definitions[w.definition_id].target_mode, w.target_id,
        )) for w in active
    }
    targets = tuple(t for t in (definition.bind_target(r) for r in references)
                    if (definition.goal, t) not in occupied)
    return _Candidate(definition, targets, weight) if targets else None


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
    anchors = dict(state.last_created_by_area)
    next_id = state.next_instance_id
    while len(active) < BALANCE.integer("wishes", "maximum_active"):
        candidates: dict[WishArea, list[_Candidate]] = {}
        for definition in definitions.values():
            candidate = _candidate(definition, elapsed=elapsed, context=context,
                                   active=active, definitions=definitions)
            if candidate is not None:
                candidates.setdefault(definition.area, []).append(candidate)
        if not candidates:
            break
        areas = tuple(candidates)
        area = rng.choices(areas, weights=[wish_area_weight(a, needs) for a in areas],
                           k=1)[0]
        forms = candidates[area]
        candidate = rng.choices(forms, weights=[c.weight for c in forms], k=1)[0]
        definition = candidate.definition
        if next_id >= 2**63 - 1:
            raise ValueError("Wish instance allocation exhausted")
        target = rng.choice(candidate.targets)
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
