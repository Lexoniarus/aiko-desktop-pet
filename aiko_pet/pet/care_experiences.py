"""Pure recording of real personal experiences in the existing Pet evidence.

Encounters are care visits separated by two hours without pleasant contact.
Wish assignment is not fulfillment: only a successful outcome sets the saved
wish identity. No needs refill, timer or autonomous intake invents a visit.
"""

from dataclasses import replace

from .care_evidence import (
    MAX_CARE_ENCOUNTERS,
    MAX_CARE_EXPERIENCES,
    CareActivity,
    CareEncounter,
    CareEvidenceState,
    CareExperience,
)
from .moodlet_catalog import MOODLET_CATALOG
from .moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    reinforce_moodlet,
)

ENCOUNTER_GAP_SECONDS = 2 * 3600
EVERYDAY_GAPS = {
    CareActivity.SOCIAL: (4 * 3600, MoodletId.CONNECTION),
    CareActivity.PETTING: (4 * 3600, MoodletId.SECURE),
}


def record_experience(
    state: MoodletState,
    event: CareExperience,
) -> tuple[MoodletState, bool]:
    """Reject replays and link welcome contact to one bounded care visit."""
    evidence = state.care_evidence or CareEvidenceState(event.occurred_at)
    if any(e.receipt_id == event.receipt_id for e in evidence.experiences):
        return state, False
    encounters = evidence.encounters
    next_id = evidence.next_encounter_id
    if event.pleasant:
        if (
            encounters
            and event.occurred_at - encounters[-1].last_activity_at
            < ENCOUNTER_GAP_SECONDS
        ):
            encounter = replace(
                encounters[-1],
                last_activity_at=max(
                    encounters[-1].last_activity_at,
                    event.occurred_at,
                ),
            )
            encounters = (*encounters[:-1], encounter)
        else:
            encounter = CareEncounter(next_id, event.occurred_at, event.occurred_at)
            next_id += 1
            encounters = (*encounters, encounter)
        event = replace(event, encounter_id=encounter.instance_id)
    events = tuple(sorted((*evidence.experiences, event), key=lambda e: e.occurred_at))[
        -MAX_CARE_EXPERIENCES:
    ]
    encounters = encounters[-MAX_CARE_ENCOUNTERS:]
    retained_ids = {e.instance_id for e in encounters}
    events = tuple(
        e for e in events if e.encounter_id is None or e.encounter_id in retained_ids
    )
    # Under sustained overflow, incomplete evidence is unknown, never a good day.
    baseline = evidence.baseline
    progress = tuple(
        replace(p, awake_contact_gap_seconds=0) if event.pleasant else p
        for p in evidence.progress
    )
    if len(evidence.experiences) >= MAX_CARE_EXPERIENCES:
        baseline = max(baseline, events[0].occurred_at)
        progress = tuple(p for p in progress if p.period_start >= baseline)
        encounters = tuple(e for e in encounters if e.started_at >= baseline)
        retained_ids = {e.instance_id for e in encounters}
        events = tuple(
            replace(e, encounter_id=None) if e.encounter_id not in retained_ids else e
            for e in events
        )
    return replace(
        state,
        care_evidence=replace(
            evidence,
            baseline=baseline,
            next_encounter_id=next_id,
            encounters=encounters,
            experiences=events,
            progress=progress,
        ),
    ), True


def event_has_wish_outcome(state: MoodletState, receipt: str) -> bool:
    return (
        any(
            e.receipt_id == receipt and e.wish_instance_id is not None
            for e in state.care_evidence.experiences
        )
        if state.care_evidence is not None
        else False
    ) or any(
        c.event_id == receipt and c.kind == MoodletCauseKind.WISH_FULFILLED
        for episode in state.active
        for c in episode.causes
    )


def award_everyday_experience(
    before: MoodletState,
    state: MoodletState,
    event: CareExperience,
) -> MoodletState:
    """Gap credit uses actual activities, including previously wished-for ones."""
    rule = EVERYDAY_GAPS.get(event.activity)
    if (
        rule is None
        or not event.pleasant
        or event_has_wish_outcome(
            state,
            event.receipt_id,
        )
    ):
        return state
    evidence = before.care_evidence
    if evidence is None:
        return state  # No reliable history before the first recorded event.
    previous = max(
        (e.occurred_at for e in evidence.experiences if e.activity == event.activity),
        default=evidence.baseline,
    )
    seconds, family = rule
    if event.occurred_at - previous < seconds:
        return state
    return award_positive(state, family, event)


def award_positive(
    state: MoodletState,
    family: MoodletId,
    event: CareExperience,
    *,
    elapsed: float | None = None,
) -> MoodletState:
    at = event.occurred_at if elapsed is None else elapsed
    return reinforce_moodlet(
        state,
        family,
        elapsed=at,
        definitions=MOODLET_CATALOG.definitions,
        attribution=MoodletAttribution.USER,
        cause=MoodletCause(
            MoodletCauseKind.INTERACTION,
            at,
            event.receipt_id,
            MoodletAttribution.USER,
            target_id=event.target_id,
            outcome=event.outcome,
            object_id=event.object_id,
        ),
    )


def award_comeback(state: MoodletState, receipt: str) -> MoodletState:
    evidence = state.care_evidence
    if evidence is None or event_has_wish_outcome(state, receipt):
        return state
    event = next(e for e in evidence.experiences if e.receipt_id == receipt)
    rounds = [
        e
        for e in evidence.experiences
        if e.activity == CareActivity.PLAY
        and e.target_id == event.target_id
        and e.occurred_at <= event.occurred_at
    ]
    index = rounds.index(event)
    if (
        event.outcome == MoodletOutcome.WIN
        and index >= 2
        and all(e.outcome == MoodletOutcome.LOSS for e in rounds[index - 2 : index])
    ):
        return award_positive(state, MoodletId.PRIDE, event)
    return state


def complete_play_session(
    state: MoodletState,
    *,
    game_id: str,
    session_id: str,
    last_receipt: str,
    elapsed: float,
) -> MoodletState:
    """Enrich the actual final round; never create a second session reward fact."""
    evidence = state.care_evidence
    if evidence is None:
        return state
    prefix = f"play:{game_id}:{session_id}:"
    rounds = [e for e in evidence.experiences if e.receipt_id.startswith(prefix)]
    if len(rounds) < 2 or rounds[-1].receipt_id != last_receipt:
        return state
    last = rounds[-1]
    if last.pleasant:
        return state
    # Reinsert the final round with welcome-visit metadata, preserving its order.
    without = replace(
        state,
        care_evidence=replace(
            evidence,
            experiences=tuple(e for e in evidence.experiences if e != last),
        ),
    )
    state, _ = record_experience(without, replace(last, pleasant=True))
    updated = state.care_evidence
    assert updated is not None
    # Earlier fulfilled round goals belong to this real shared visit too.
    encounter_id = updated.experiences[-1].encounter_id
    encounters = tuple(
        replace(e, started_at=min(e.started_at, rounds[0].occurred_at))
        if e.instance_id == encounter_id
        else e
        for e in updated.encounters
    )
    state = replace(
        state,
        care_evidence=replace(
            updated,
            encounters=encounters,
            experiences=tuple(
                replace(e, encounter_id=encounter_id) if e in rounds else e
                for e in updated.experiences
            ),
        ),
    )
    previous = max(
        (
            e.occurred_at
            for e in evidence.experiences
            if e.activity == CareActivity.PLAY and not e.receipt_id.startswith(prefix)
        ),
        default=evidence.baseline,
    )
    rewarded = event_has_wish_outcome(state, last_receipt) or any(
        c.event_id == last_receipt
        for ep in state.active
        for c in ep.causes
        if c.kind in (MoodletCauseKind.INTERACTION, MoodletCauseKind.WISH_FULFILLED)
    )
    if rounds[0].occurred_at - previous >= 2 * 3600 and not rewarded:
        state = award_positive(state, MoodletId.SHARED_PLAY, last, elapsed=elapsed)
    return state
