"""Qualify bounded care periods on Pet's existing chronological time path.

This policy neither simulates user actions nor owns another clock/history.
Completed periods consume their evidence once; retained impressions decay by
the ordinary Moodlet policy, including sleep and unobserved elapsed time.
"""

from dataclasses import replace

from .balance import BALANCE
from .care_evidence import (
    CareEvidenceState,
    CareExperience,
    CarePeriodSummary,
    LongTermProgress,
)
from .friendship_history import FriendshipHistory
from .moodlet_catalog import MOODLET_CATALOG
from .moodlet_patterns import (
    AppreciationParameters,
    GuardedParameters,
    OptimismParameters,
    OverlookedParameters,
    TrustParameters,
    UncertaintyParameters,
)
from .moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletGroup,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    reinforce_moodlet,
)
from .need_exposure import exposure_totals
from .wishes import WishArea


def prepare_long_term(state: MoodletState, *, elapsed: float) -> MoodletState:
    evidence = state.care_evidence or CareEvidenceState(elapsed)
    known = {p.definition_id for p in evidence.progress}
    progress = tuple(
        LongTermProgress(d.id, elapsed, elapsed, elapsed)
        for d in MOODLET_CATALOG.definitions.values()
        if d.group == MoodletGroup.LONG_TERM and d.id not in known
    )
    return replace(
        state,
        care_evidence=replace(
            evidence,
            progress=(*evidence.progress, *progress),
        ),
    )


def next_long_term_boundary(state: MoodletState, *, elapsed: float) -> float:
    evidence = state.care_evidence
    if evidence is None or not evidence.progress:
        return float("inf")
    period = MOODLET_CATALOG.long_term_policy.period_seconds
    return max(1e-9, min(p.period_start + period - elapsed for p in evidence.progress))


def _spaced(times: list[float], count: int, gap: float, span: float = 0) -> bool:
    """Earliest admissible contacts maximize the remaining available span."""
    if not times:
        return False
    chosen = [times[0]]
    for at in times[1:]:
        if at - chosen[-1] >= gap:
            chosen.append(at)
    return len(chosen) >= count and chosen[-1] - chosen[0] >= span


def _uncertainty_pairs(events: tuple[CareExperience, ...], gap: int) -> int:
    available: set[int] = set()
    used: set[int] = set()
    last = float("-inf")
    pairs = 0
    for event in events:
        if event.pleasant and event.encounter_id is not None:
            available.add(event.encounter_id)
        if not event.upsetting or event.occurred_at - last < gap:
            continue
        candidates = available - used
        if candidates:
            used.add(min(candidates))
            last = event.occurred_at
            pairs += 1
    return pairs


def _exposure_level(history: FriendshipHistory, elapsed: float) -> int:
    critical, zero = exposure_totals(history.critical, elapsed)
    return max(
        (
            level
            for level, name in enumerate(("one", "two", "three"), 1)
            if max(critical)
            >= BALANCE.number(
                "moodlets",
                f"critical_level_{name}_seconds",
            )
            - 1e-7
            or max(zero)
            >= BALANCE.number(
                "moodlets",
                f"zero_level_{name}_seconds",
            )
            - 1e-7
        ),
        default=0,
    )


def _summarize(
    evidence: CareEvidenceState,
    progress: LongTermProgress,
    history: FriendshipHistory,
    elapsed: float,
) -> tuple[CarePeriodSummary, tuple[CareExperience, ...], list[float]]:
    events = tuple(
        e
        for e in evidence.experiences
        if progress.period_start <= e.occurred_at < elapsed
    )
    pleasant = tuple(e for e in events if e.pleasant)
    encounter_ids = {e.encounter_id for e in pleasant if e.encounter_id is not None}
    # The first actual welcome activity in this period represents its encounter.
    times = [
        min(e.occurred_at for e in pleasant if e.encounter_id == identity)
        for identity in encounter_ids
    ]
    wishes = {e.wish_instance_id: e for e in events if e.wish_instance_id is not None}
    upsetting = tuple(e for e in events if e.upsetting)
    pairs = _uncertainty_pairs(events, 2 * 3600)
    summary = CarePeriodSummary(
        progress.period_start,
        elapsed,
        len(encounter_ids),
        tuple(sorted({e.activity for e in pleasant})),
        len(wishes),
        tuple(sorted({e.area for e in wishes.values() if e.area is not None})),
        sum(
            e.outcome == MoodletOutcome.WIN
            or e.wish_instance_id is not None
            and e.area == WishArea.GAMES
            for e in events
        ),
        len(upsetting),
        sum(e.boundary_violated for e in upsetting),
        pairs,
        progress.longest_awake_contact_gap_seconds,
        _exposure_level(history, elapsed),
    )
    return summary, events, sorted(times)


def _qualifies(
    parameters: object,
    summary: CarePeriodSummary,
    events: tuple[CareExperience, ...],
    times: list[float],
) -> bool:
    if isinstance(parameters, TrustParameters):
        return (
            summary.boundary_violations <= parameters.maximum_boundary_violations
            and summary.care_exposure_level < parameters.care_exposure_level_limit
            and len(summary.activity_kinds) >= parameters.minimum_activity_kinds
            and _spaced(
                times,
                parameters.minimum_encounters,
                parameters.minimum_encounter_gap_seconds,
                parameters.minimum_encounter_span_seconds,
            )
        )
    if isinstance(parameters, AppreciationParameters):
        wish_contacts = sorted(
            {
                e.encounter_id: e.occurred_at
                for e in events
                if e.wish_instance_id is not None and e.encounter_id is not None
            }.values()
        )
        return (
            summary.fulfilled_wishes >= parameters.minimum_fulfilled_wishes
            and len(summary.wish_areas) >= parameters.minimum_wish_areas
            and summary.boundary_violations <= parameters.maximum_boundary_violations
            and _spaced(
                wish_contacts,
                parameters.minimum_encounters,
                parameters.minimum_encounter_gap_seconds,
            )
        )
    if isinstance(parameters, OptimismParameters):
        activities = {
            (e.encounter_id, e.activity)
            for e in events
            if e.pleasant and e.encounter_id is not None
        }
        return (
            len(activities) >= parameters.minimum_pleasant_activities
            and len({e.area for e in events if e.pleasant})
            >= parameters.minimum_activity_areas
            and summary.successes >= parameters.minimum_successes
            and _spaced(
                times,
                parameters.minimum_encounters,
                parameters.minimum_encounter_gap_seconds,
            )
        )
    if isinstance(parameters, UncertaintyParameters):
        return (
            _uncertainty_pairs(events, parameters.minimum_incident_gap_seconds)
            >= parameters.minimum_pairs
        )
    if isinstance(parameters, OverlookedParameters):
        return (
            summary.encounters <= parameters.maximum_encounters
            and summary.awake_contact_gap_seconds
            >= parameters.awake_contact_gap_seconds
        )
    if isinstance(parameters, GuardedParameters):
        incidents = [e.occurred_at for e in events if e.upsetting]
        return (
            len(incidents) >= parameters.minimum_incidents
            and incidents[-1] - incidents[0] >= parameters.minimum_incident_span_seconds
        )
    return False


def advance_long_term(
    state: MoodletState,
    history: FriendshipHistory,
    *,
    elapsed: float,
    sleeping: bool,
) -> MoodletState:
    """Account one existing integration interval, evaluate before pruning."""
    evidence = state.care_evidence
    assert evidence is not None
    period = MOODLET_CATALOG.long_term_policy.period_seconds
    cursors = []
    completed = False
    for cursor in evidence.progress:
        if elapsed < cursor.last_accounted_at:
            raise ValueError("Care evidence cannot move backwards")
        awake = not sleeping and elapsed > cursor.last_accounted_at
        gap = cursor.awake_contact_gap_seconds
        if awake:
            gap += elapsed - cursor.last_accounted_at
        cursor = replace(
            cursor,
            last_accounted_at=elapsed,
            awake_contact_gap_seconds=gap,
            longest_awake_contact_gap_seconds=(
                max(
                    cursor.longest_awake_contact_gap_seconds,
                    gap,
                )
                if awake
                else cursor.longest_awake_contact_gap_seconds
            ),
        )
        if elapsed >= cursor.period_start + period - 1e-7:
            completed = True
            endpoint = elapsed
            summary, events, times = _summarize(evidence, cursor, history, endpoint)
            definition = MOODLET_CATALOG.definitions[cursor.definition_id]
            qualified = _qualifies(definition.parameters, summary, events, times)
            if qualified:
                state = reinforce_moodlet(
                    state,
                    definition.id,
                    elapsed=elapsed,
                    definitions=MOODLET_CATALOG.definitions,
                    attribution=MoodletAttribution.USER,
                    cause=MoodletCause(
                        MoodletCauseKind.LONG_TERM,
                        elapsed,
                        f"period:{definition.id}:{cursor.period_start}",
                        MoodletAttribution.USER,
                        outcome=MoodletOutcome.COMPLETED,
                        period=summary,
                    ),
                )
            carry = (
                gap if definition.id == MoodletId.OVERLOOKED and not qualified else 0.0
            )
            cursor = LongTermProgress(
                definition.id,
                endpoint,
                endpoint,
                elapsed,
                carry,
            )
        cursors.append(cursor)
    if not completed:
        return replace(
            state,
            care_evidence=replace(
                evidence,
                progress=tuple(cursors),
            ),
        )
    # Retain the current period plus the latest actual activity of each kind and
    # last two rounds per game for gap/comeback queries, not a permanent archive.
    cutoff = min(p.period_start for p in cursors)
    keep: set[str] = set()
    seen: dict[tuple[object, ...], int] = {}
    for event in reversed(evidence.experiences):
        key = (event.activity, event.target_kind, event.target_id)
        count = seen.get(key, 0)
        if event.occurred_at >= cutoff or count < 2:
            keep.add(event.receipt_id)
        seen[key] = count + 1
    events = tuple(e for e in evidence.experiences if e.receipt_id in keep)
    encounters = tuple(
        e
        for e in evidence.encounters
        if any(v.encounter_id == e.instance_id for v in events)
    )
    return replace(
        state,
        care_evidence=replace(
            evidence,
            progress=tuple(cursors),
            experiences=events,
            encounters=encounters,
        ),
    )
