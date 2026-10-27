"""Pure application of qualified cursor facts on the existing pet elapsed axis."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Mapping

from .interaction_events import CursorExperience
from .moodlet_models import (
    MoodletCause,
    MoodletCauseKind,
    MoodletDefinition,
    MoodletEpisode,
    MoodletGroup,
    MoodletState,
)
from .moodlet_timing import initial_stage_seconds
from .moodlet_types import MoodletId, MoodletOutcome


def apply_cursor_experience(
    state: MoodletState,
    event: CursorExperience,
    *,
    elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """Absolute strength, bounded receipts, no care/wish/relationship side effects."""
    if (
        not isinstance(event, CursorExperience)
        or not math.isfinite(elapsed)
        or elapsed < state.baseline
    ):
        raise ValueError("Invalid cursor experience endpoint")
    key = (
        MoodletId.CURSOR_CURIOSITY
        if event.feeling == "curiosity"
        else MoodletId.CURSOR_FEAR
    )
    definition = definitions[key]
    if definition.group != MoodletGroup.CURSOR:
        raise ValueError("Cursor evidence requires its impression family")
    prior = next((e for e in state.active if e.definition_id == key), None)
    cause = MoodletCause(
        MoodletCauseKind.CURSOR,
        elapsed,
        event.evidence_id,
        target_id="cursor",
        outcome=MoodletOutcome.COMPLETED,
    )
    if prior is not None:
        if any(c.receipt == cause.receipt for c in prior.causes):
            return state
        if elapsed < prior.last_trigger_at:
            raise ValueError("Cursor evidence cannot precede its last trigger")
        level = max(prior.level, event.level)
    else:
        if state.next_instance_id >= 2**63 - 1:
            raise ValueError("Moodlet allocation exhausted")
        level = event.level
    budgets = initial_stage_seconds(definition, level)
    episode = (
        replace(
            prior,
            level=level,
            last_trigger_at=elapsed,
            remaining_seconds=budgets[-1],
            lower_stage_seconds=budgets[:-1],
        )
        if prior is not None
        else MoodletEpisode(
            state.next_instance_id,
            key,
            level,
            elapsed,
            elapsed,
            budgets[-1],
            lower_stage_seconds=budgets[:-1],
        )
    )
    episode = episode.with_cause(cause)
    return replace(
        state,
        next_instance_id=state.next_instance_id + int(prior is None),
        active=tuple(episode if e.definition_id == key else e for e in state.active)
        if prior is not None
        else (*state.active, episode),
    )
