"""Qualify emotional after-effects from the existing bounded care history."""

from dataclasses import replace
from typing import Mapping

from .balance import BALANCE
from .friendship_history import NEED_NAMES, FriendshipHistory
from .moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletDefinition,
    MoodletId,
    MoodletState,
    PoorCareCursor,
    PoorCareEvidence,
    PoorCareParameters,
    reinforce_moodlet,
)
from .need_exposure import mark_exposure, unaccounted_exposure
from .needs import NeedLevels


def prepare_poor_care(
    state: MoodletState, history: FriendshipHistory, *, elapsed: float,
) -> MoodletState:
    """Initialize at the current endpoint without replaying legacy history."""
    if state.poor_care is not None or history.baseline is None:
        return state
    cursors = []
    for i in range(len(NEED_NAMES)):
        mark = mark_exposure(history.critical, elapsed, i)
        cursors.append(PoorCareCursor(mark, mark))
    return replace(state, poor_care=PoorCareEvidence(elapsed, tuple(cursors)))


def _account_recovered_burden(
    state: MoodletState, history: FriendshipHistory, *, elapsed: float,
    needs: NeedLevels, definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """A qualified recovery closes handled burden, never fresh residual time.

    Merely crossing 25 or briefly reaching 40 is not emotional recovery. Until
    qualification, disjoint deficient periods still belong to the same cycle.
    """
    evidence = state.poor_care
    if evidence is None:
        return state
    cursors = list(evidence.needs)
    for definition in definitions.values():
        parameters = definition.parameters
        if not isinstance(parameters, PoorCareParameters):
            continue
        i = NEED_NAMES.index(parameters.need)
        cursor = cursors[i]
        if not cursor.exposed or getattr(needs, parameters.need) < BALANCE.number(
            "moodlets", "recovery_need_threshold",
        ):
            continue
        episode = next((e for e in state.active
                        if e.definition_id == definition.id), None)
        if episode is not None and (
            episode.recovery_since is None or elapsed - episode.recovery_since
            < BALANCE.number("moodlets", "recovery_stable_seconds") - 1e-7
        ):
            continue
        mark = (mark_exposure(history.critical, elapsed, i)
                if cursor.handled_level == 3 else cursor.handled)
        cursors[i] = PoorCareCursor(mark, mark)
    updated = replace(evidence, needs=tuple(cursors))
    return state if updated == evidence else replace(state, poor_care=updated)


def _exposed(before: float, after: float, index: int, sleeping: bool) -> bool:
    return ((before + after) / 2 < BALANCE.number("friendship", "critical_need")
            and not (index == 1 and sleeping and after > before))


def _thresholds(route: str) -> tuple[float, ...]:
    return tuple(BALANCE.number("moodlets", f"{route}_level_{level}_seconds")
                 for level in ("one", "two", "three"))


def poor_care_at_capacity(
    state: MoodletState, needs: NeedLevels, *, sleeping: bool,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> bool:
    """A constant zero-needs stretch at every cap has no new emotional work.

    The real history continues to advance. Its handled stretch is closed by
    qualified recovery when supply or sleep changes the next numeric interval.
    """
    evidence = state.poor_care
    return (not sleeping and evidence is not None
            and len(state.active) == len(NEED_NAMES)
            and all(getattr(needs, name) == 0 for name in NEED_NAMES)
            and all(c.handled_level == 3 and c.exposed for c in evidence.needs)
            and sum(isinstance(definitions[e.definition_id].parameters,
                               PoorCareParameters)
                    and e.decay_paused and e.recovery_since is None
                    and e.level == len(definitions[e.definition_id].level_points)
                    for e in state.active) == len(NEED_NAMES))


def next_poor_care_boundary(
    state: MoodletState, history: FriendshipHistory, *, elapsed: float, seconds: float,
    before: NeedLevels, after: NeedLevels, sleeping: bool,
) -> float:
    """Split only a genuinely reachable new threshold; no old-burden replay."""
    if state.poor_care is None:
        return seconds
    boundary = seconds
    for i, name in enumerate(NEED_NAMES):
        cursor = state.poor_care.needs[i]
        low, high = float(getattr(before, name)), float(getattr(after, name))
        if cursor.handled_level == 3 or not _exposed(low, high, i, sleeping):
            continue
        for route, index in (("critical", 0), ("zero", 1)):
            if index and (low != 0 or high != 0):
                continue
            threshold = _thresholds(route)[cursor.handled_level]

            def total(at: float) -> float:
                return unaccounted_exposure(
                    history.critical, elapsed + at, i, cursor.accounted,
                )[index] + at

            if total(boundary) < threshold - 1e-7:
                continue
            left, right = 0.0, boundary
            # Read the existing rolling history; no speculative need simulation.
            for _ in range(36):
                middle = (left + right) / 2
                if total(middle) < threshold:
                    left = middle
                else:
                    right = middle
            boundary = max(1e-7, right)
    return boundary


def qualify_poor_care(
    state: MoodletState, history: FriendshipHistory, *, elapsed: float,
    before: NeedLevels, after: NeedLevels, sleeping: bool,
    definitions: Mapping[MoodletId, MoodletDefinition],
) -> MoodletState:
    """Handle each fresh burden level once, without direct friendship effects."""
    state = _account_recovered_burden(
        state, history, elapsed=elapsed, needs=after, definitions=definitions,
    )
    evidence = state.poor_care
    if evidence is None:
        return state
    cursors = list(evidence.needs)
    for definition in definitions.values():
        parameters = definition.parameters
        if not isinstance(parameters, PoorCareParameters):
            continue
        i = NEED_NAMES.index(parameters.need)
        low, high = float(getattr(before, parameters.need)), float(
            getattr(after, parameters.need)
        )
        if not _exposed(low, high, i, sleeping):
            continue
        cursor = cursors[i]
        episode = next((e for e in state.active
                        if e.definition_id == definition.id), None)
        if episode is not None and episode.level == len(definition.level_points):
            # At the cap the current stretch is represented in full. Close its
            # watermark only when the stretch ends, without per-tick refresh.
            if cursor.handled_level != 3 or not cursor.exposed:
                cursors[i] = replace(cursor, handled=mark_exposure(
                    history.critical, elapsed, i,
                ), handled_level=3, exposed=True)
            continue
        critical, zero = unaccounted_exposure(
            history.critical, elapsed, i, cursor.accounted,
        )
        level = max((index for index, (c, z) in enumerate(zip(
            _thresholds("critical"), _thresholds("zero"), strict=True,
        ), 1) if critical >= c - 1e-7 or zero >= z - 1e-7), default=0)
        cursor = replace(cursor, exposed=True)
        if level > cursor.handled_level:
            if episode is None or level > episode.level:
                state = reinforce_moodlet(
                    state, definition.id, elapsed=elapsed,
                    definitions=definitions, level=level,
                    cause=MoodletCause(
                        MoodletCauseKind.POOR_CARE, elapsed,
                        f"poor_care:{parameters.need}:{float(cursor.accounted.at)}:{level}",
                        target_id=parameters.need,
                    ),
                )
            cursor = replace(
                cursor, handled=mark_exposure(history.critical, elapsed, i),
                handled_level=level,
            )
        cursors[i] = cursor
    updated = replace(evidence, needs=tuple(cursors))
    return state if updated == state.poor_care else replace(state, poor_care=updated)
