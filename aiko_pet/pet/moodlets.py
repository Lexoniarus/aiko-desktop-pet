"""Pure Moodlet transitions, contributions and relief on Pet's elapsed axis."""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Mapping

from .balance import BALANCE
from .moodlet_models import (
    MAX_MOODLET_CAUSES as MAX_MOODLET_CAUSES,
)
from .moodlet_models import (
    EmotionalDirection as EmotionalDirection,
)
from .moodlet_models import (
    FoodMonotonyParameters as FoodMonotonyParameters,
)
from .moodlet_models import (
    MoodletAttribution as MoodletAttribution,
)
from .moodlet_models import (
    MoodletCause as MoodletCause,
)
from .moodlet_models import (
    MoodletCauseKind as MoodletCauseKind,
)
from .moodlet_models import (
    MoodletContributions as MoodletContributions,
)
from .moodlet_models import (
    MoodletDecay as MoodletDecay,
)
from .moodlet_models import (
    MoodletDefinition as MoodletDefinition,
)
from .moodlet_models import (
    MoodletEpisode as MoodletEpisode,
)
from .moodlet_models import (
    MoodletGameResult as MoodletGameResult,
)
from .moodlet_models import (
    MoodletGroup as MoodletGroup,
)
from .moodlet_models import (
    MoodletParameters as MoodletParameters,
)
from .moodlet_models import (
    MoodletPolarity as MoodletPolarity,
)
from .moodlet_models import (
    MoodletState as MoodletState,
)
from .moodlet_models import (
    MoodletWishCause as MoodletWishCause,
)
from .moodlet_models import (
    PettingParameters as PettingParameters,
)
from .moodlet_models import (
    PettingTolerance as PettingTolerance,
)
from .moodlet_models import (
    PokingParameters as PokingParameters,
)
from .moodlet_models import (
    PoorCareCursor as PoorCareCursor,
)
from .moodlet_models import (
    PoorCareEvidence as PoorCareEvidence,
)
from .moodlet_models import (
    PoorCareParameters as PoorCareParameters,
)
from .moodlet_models import (
    RelocationParameters as RelocationParameters,
)
from .moodlet_models import (
    WithholdingParameters as WithholdingParameters,
)
from .moodlet_patterns import LongTermMoodletPolicy
from .moodlet_timing import age_moodlet, initial_stage_seconds, reinforced_stage_seconds
from .moodlet_types import MoodletId as MoodletId
from .moodlet_types import MoodletOutcome as MoodletOutcome
from .needs import NeedLevels


def calculate_moodlet_contributions(
    state: MoodletState, *, definitions: Mapping[MoodletId, MoodletDefinition],
    long_term_policy: LongTermMoodletPolicy,
) -> MoodletContributions:
    if not state.active:
        return MoodletContributions()
    groups: dict[MoodletGroup, float] = {}
    long_positive = long_negative = 0.0
    for episode in state.active:
        definition = definitions[episode.definition_id]
        points = definition.level_points[episode.level - 1]
        if definition.group == MoodletGroup.LONG_TERM:
            long_positive += max(0, points)
            long_negative += min(0, points)
            continue
        groups[definition.group] = (groups.get(definition.group, 0)
                                    + points)
    for group, field in (
        (MoodletGroup.GAME_WISH, "game_wish_cap_points"),
        (MoodletGroup.SOCIAL_WISH, "social_wish_cap_points"),
        (MoodletGroup.POOR_CARE, "poor_care_cap_points"),
    ):
        value = groups.get(group, 0)
        limit = BALANCE.number("moodlets", field)
        groups[group] = max(-limit, min(limit, value))
    return MoodletContributions(
        min(BALANCE.number("moodlets", "positive_cap_points"),
            sum(max(0, value) for value in groups.values())
            + min(long_term_policy.positive_mood_cap_points, long_positive)),
        max(-BALANCE.number("moodlets", "negative_cap_points"),
            sum(min(0, value) for value in groups.values())
            + max(-long_term_policy.negative_mood_cap_points, long_negative)),
    )


def _recover_episode(
    episode: MoodletEpisode, definition: MoodletDefinition, *, elapsed: float,
    seconds: float, before: NeedLevels, after: NeedLevels,
) -> MoodletEpisode | None:
    parameters = definition.parameters
    assert isinstance(parameters, PoorCareParameters)
    low = float(getattr(before, parameters.need))
    high = float(getattr(after, parameters.need))
    threshold = BALANCE.number("moodlets", "recovery_need_threshold")
    end = elapsed + seconds
    if low < threshold and high < threshold:
        if episode.decay_paused and episode.recovery_since is None:
            return episode
        return replace(episode, decay_paused=True, recovery_since=None)
    healthy_start, healthy_end = elapsed, end
    if low < threshold <= high:
        healthy_start += seconds * (threshold - low) / (high - low)
    elif high < threshold <= low:
        healthy_end = elapsed + seconds * (threshold - low) / (high - low)
    since = (episode.recovery_since
             if low >= threshold and episode.recovery_since is not None
             else healthy_start)
    ready = since + BALANCE.number("moodlets", "recovery_stable_seconds")
    recovered = age_moodlet(
        episode, max(0, healthy_end - max(healthy_start, ready)), definition,
    )
    if recovered is None:
        return None
    return replace(recovered, decay_paused=high < threshold or end < ready,
                   recovery_since=since if high >= threshold else None)


def advance_moodlets(
    state: MoodletState, seconds: float, *, elapsed: float,
    before: NeedLevels, after: NeedLevels,
    definitions: Mapping[MoodletId, MoodletDefinition], observed: bool = True,
) -> MoodletState:
    """Age existing impressions over the owner's interval; never create one.

    Need trajectories are linear within a numeric step. Unobserved time cannot
    extend observed withholding, but still advances quiet-time after-effects.
    """
    if (not math.isfinite(seconds) or seconds < 0 or not math.isfinite(elapsed)
            or elapsed < state.baseline):
        raise ValueError("Moodlet progression requires a finite elapsed interval")
    if not state.active:
        return state
    active = []
    for episode in state.active:
        definition = definitions[episode.definition_id]
        if definition.decay == MoodletDecay.STABLE_RECOVERY:
            result = _recover_episode(episode, definition, elapsed=elapsed,
                                      seconds=seconds, before=before, after=after)
        else:
            paused = episode.decay_paused and observed
            current = (episode if paused == episode.decay_paused
                       else replace(episode, decay_paused=paused))
            result = age_moodlet(current, 0 if paused else seconds, definition)
        if result is not None:
            active.append(result)
    values = tuple(active)
    return state if values == state.active else replace(state, active=values)


def next_moodlet_boundary(
    state: MoodletState, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> float:
    """Seconds to the next tier/qualification change, on the existing clock."""
    boundary = math.inf
    for episode in state.active:
        definition = definitions[episode.definition_id]
        if definition.decay == MoodletDecay.STABLE_RECOVERY:
            if episode.recovery_since is None:
                continue
            wait = (episode.recovery_since
                    + BALANCE.number("moodlets", "recovery_stable_seconds") - elapsed)
            if wait > 0:
                boundary = min(boundary, wait)
                continue
        elif episode.decay_paused:
            continue
        boundary = min(boundary, episode.remaining_seconds)
    return boundary


def reinforce_moodlet(
    state: MoodletState, definition_id: MoodletId, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition], level: int = 1,
    attribution: MoodletAttribution = MoodletAttribution.UNKNOWN,
    cause: MoodletCause | None = None,
) -> MoodletState:
    """Apply already-qualified evidence at an already-advanced pet endpoint.

    Owners in later steps qualify events and reject duplicate delivery. Here
    level is the wish fulfillment strength or newly qualified poor-care level.
    Repeated-poke/petting escalation counts only subsequent qualifying events.
    """
    definition = definitions[definition_id]
    maximum = len(definition.level_points)
    if (not math.isfinite(elapsed) or elapsed < state.baseline
            or type(level) is not int or not 1 <= level <= maximum):
        raise ValueError("Invalid Moodlet trigger time or strength")
    if (definition.group in (MoodletGroup.INTERACTION, MoodletGroup.LONG_TERM)
            and level != 1):
        raise ValueError("Interaction/period evidence starts at one intensity level")
    active = list(state.active)
    for index, episode in enumerate(active):
        if episode.definition_id != definition_id:
            continue
        if cause is not None and any(c.receipt == cause.receipt
                                     for c in episode.causes):
            return state
        if elapsed < episode.last_trigger_at:
            raise ValueError("Moodlet evidence cannot precede its last trigger")
        parameters = definition.parameters
        pending = 0
        if isinstance(parameters, PoorCareParameters):
            if level <= episode.level:
                return state
            intensity = level
        elif isinstance(parameters, (PokingParameters, PettingParameters)):
            limit = (parameters.escalation_pokes
                     if isinstance(parameters, PokingParameters)
                     else parameters.escalation_attempts)
            pending = episode.pending_repetitions + 1
            intensity = min(maximum, episode.level + int(pending >= limit))
            pending = 0 if pending >= limit or intensity == maximum else pending
        else:
            intensity = min(maximum, episode.level + level)
        budgets = (reinforced_stage_seconds(episode, definition, intensity)
                   if definition.uses_positive_stage_budgets
                   else initial_stage_seconds(definition, intensity))
        active[index] = replace(
            episode, level=intensity, last_trigger_at=elapsed,
            remaining_seconds=budgets[-1],
            lower_stage_seconds=budgets[:-1]
            if definition.uses_positive_stage_budgets else (),
            pending_repetitions=pending, recovery_since=None,
            decay_paused=definition.decay != MoodletDecay.QUIET_TIME,
            attribution=attribution,
        )
        if cause is not None:
            active[index] = active[index].with_cause(cause)
        return replace(state, active=tuple(active))
    if state.next_instance_id >= 2**63 - 1:
        raise ValueError("Moodlet instance allocation exhausted")
    budgets = initial_stage_seconds(definition, level)
    episode = MoodletEpisode(
        state.next_instance_id, definition_id, level, elapsed, elapsed,
        budgets[-1],
        decay_paused=definition.decay != MoodletDecay.QUIET_TIME,
        attribution=attribution,
        lower_stage_seconds=budgets[:-1]
        if definition.uses_positive_stage_budgets else (),
    )
    if cause is not None:
        episode = episode.with_cause(cause)
    return replace(state, next_instance_id=state.next_instance_id + 1,
                   active=(*state.active, episode))


def resolve_moodlet_cause(
    state: MoodletState, instance_id: int, *,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """Ending observed withholding permits decay; it does not erase emotion."""
    return replace(state, active=tuple(
        replace(e, decay_paused=False)
        if e.instance_id == instance_id
        and definitions[e.definition_id].decay == MoodletDecay.RESOLVED_QUIET_TIME
        else e for e in state.active
    ))


def relieve_moodlet(
    state: MoodletState, instance_id: int, *, elapsed: float,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """One qualified completed helpful action credits only its current tier.

    Matching activities, intake, search resolution and action acceptance are
    supplied by their semantic owners in later steps, never inferred here.
    """
    if not math.isfinite(elapsed) or elapsed < state.baseline:
        raise ValueError("Invalid Moodlet relief time")
    active = []
    for episode in state.active:
        definition = definitions[episode.definition_id]
        eligible = (episode.instance_id == instance_id and definition.relief_seconds > 0
                    and episode.level not in episode.relieved_levels
                    and not episode.decay_paused)
        if episode.definition_id in (MoodletId.POKING, MoodletId.CROWDED):
            eligible = eligible and elapsed - episode.last_trigger_at >= BALANCE.number(
                "moodlets", "relief_quiet_seconds",
            )
        if definition.decay == MoodletDecay.STABLE_RECOVERY:
            eligible = (eligible and episode.recovery_since is not None
                        and elapsed - episode.recovery_since >= BALANCE.number(
                            "moodlets", "recovery_stable_seconds",
                        ))
        result: MoodletEpisode | None = episode
        if eligible:
            result = age_moodlet(replace(
                episode, relieved_levels=(*episode.relieved_levels, episode.level),
            ), min(episode.remaining_seconds, definition.relief_seconds), definition)
        if result is not None:
            active.append(result)
    return replace(state, active=tuple(active))
