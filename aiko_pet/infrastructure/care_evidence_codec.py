"""Strict storage of bounded encounters, semantic receipts and period watermarks."""

import math
from dataclasses import asdict
from typing import Any

from ..games.contracts import GameId
from ..pet.care_evidence import (
    MAX_CARE_ENCOUNTERS,
    MAX_CARE_EXPERIENCES,
    CareActivity,
    CareEncounter,
    CareEvidenceState,
    CareExperience,
    CarePeriodSummary,
    LongTermProgress,
)
from ..pet.catalog_validation import (
    enum_value,
    integer_value,
    number_value,
    object_fields,
)
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.moodlets import MoodletGroup, MoodletId, MoodletOutcome
from ..pet.wishes import WishArea, WishTargetKind


def _rows(raw: Any, maximum: int) -> list[Any]:
    if not isinstance(raw, list) or len(raw) > maximum:
        raise ValueError("Unbounded care evidence")
    return raw


def _token(raw: Any) -> str:
    if not isinstance(raw, str) or not 1 <= len(raw) <= 128:
        raise ValueError("Invalid care evidence identity")
    return raw


def decode_period_summary(
    raw: Any, baseline: float, elapsed: float
) -> CarePeriodSummary:
    row = object_fields(
        raw,
        (
            "version",
            "started_at",
            "ended_at",
            "encounters",
            "activity_kinds",
            "fulfilled_wishes",
            "wish_areas",
            "successes",
            "upsetting_incidents",
            "boundary_violations",
            "uncertainty_pairs",
            "awake_contact_gap_seconds",
            "care_exposure_level",
        ),
        context="care period summary",
    )
    integer_value(row["version"], minimum=1, maximum=1, context="care summary version")
    start = number_value(
        row["started_at"],
        minimum=baseline,
        maximum=elapsed,
        context="care period beginning",
    )
    end = number_value(
        row["ended_at"], minimum=start, maximum=elapsed, context="care period end"
    )
    if not math.isclose(
        end - start, MOODLET_CATALOG.long_term_policy.period_seconds,
        rel_tol=0, abs_tol=1e-7,
    ):
        raise ValueError("Care summary must describe one complete qualification period")
    kinds = tuple(
        enum_value(v, CareActivity, context="care summary activity")
        for v in _rows(row["activity_kinds"], len(CareActivity))
    )
    areas = tuple(
        enum_value(v, WishArea, context="care summary wish area")
        for v in _rows(row["wish_areas"], len(WishArea))
    )
    if len(set(kinds)) != len(kinds) or len(set(areas)) != len(areas):
        raise ValueError("Duplicate care summary kind or area")
    counts = tuple(
        integer_value(
            row[k], minimum=0, maximum=MAX_CARE_EXPERIENCES, context=f"care summary {k}"
        )
        for k in (
            "encounters",
            "fulfilled_wishes",
            "successes",
            "upsetting_incidents",
            "boundary_violations",
            "uncertainty_pairs",
        )
    )
    encounters, wishes, successes, incidents, boundaries, pairs = counts
    if (
        encounters > MAX_CARE_ENCOUNTERS
        or boundaries > incidents
        or pairs > incidents
        or len(areas) > wishes
    ):
        raise ValueError("Inconsistent care summary counts")
    return CarePeriodSummary(
        start,
        end,
        encounters,
        kinds,
        wishes,
        areas,
        successes,
        incidents,
        boundaries,
        pairs,
        number_value(
            row["awake_contact_gap_seconds"],
            minimum=0,
            maximum=end - baseline,
            context="care summary awake gap",
        ),
        integer_value(
            row["care_exposure_level"],
            minimum=0,
            maximum=3,
            context="care summary exposure level",
        ),
    )


def encode_period_summary(summary: CarePeriodSummary) -> dict[str, Any]:
    row = asdict(summary)
    row.update(
        version=1,
        activity_kinds=[k.value for k in summary.activity_kinds],
        wish_areas=[a.value for a in summary.wish_areas],
    )
    return row


def _experience(
    raw: Any,
    earliest: float,
    elapsed: float,
    encounters: dict[int, CareEncounter],
) -> CareExperience:
    row = object_fields(
        raw,
        (
            "receipt_id",
            "occurred_at",
            "activity",
            "outcome",
            "area",
            "target_kind",
            "target_id",
            "encounter_id",
            "wish_instance_id",
            "pleasant",
            "upsetting",
            "boundary_violated",
            "object_id",
        ),
        context="care experience",
    )
    at = number_value(
        row["occurred_at"],
        minimum=earliest,
        maximum=elapsed,
        context="care experience time",
    )
    activity = enum_value(row["activity"], CareActivity, context="care activity")
    outcome = enum_value(row["outcome"], MoodletOutcome, context="care outcome")
    area = (
        None
        if row["area"] is None
        else enum_value(
            row["area"],
            WishArea,
            context="care area",
        )
    )
    kind = (
        None
        if row["target_kind"] is None
        else enum_value(
            row["target_kind"],
            WishTargetKind,
            context="care target kind",
        )
    )
    target = None if row["target_id"] is None else _token(row["target_id"])
    object_id = None if row["object_id"] is None else _token(row["object_id"])
    if (
        (kind is None) != (target is None)
        or kind == WishTargetKind.GAME
        and target not in {g.value for g in GameId}
        or kind == WishTargetKind.FOOD
        and target not in DEFAULT_CATALOG.foods
    ):
        raise ValueError("Unknown or incomplete care experience target")
    expected = {
        CareActivity.PLAY: (WishArea.GAMES, WishTargetKind.GAME),
        CareActivity.SOCIAL: (WishArea.SOCIAL, WishTargetKind.SOCIAL),
        CareActivity.PETTING: (WishArea.AFFECTION, WishTargetKind.CARE),
        CareActivity.FOOD_HANDOVER: (WishArea.FOOD, WishTargetKind.FOOD),
    }.get(activity)
    if expected is not None and (area, kind) != expected:
        raise ValueError("Care activity has an incompatible area/target kind")
    flags = tuple(row[k] for k in ("pleasant", "upsetting", "boundary_violated"))
    if (
        any(type(v) is not bool for v in flags)
        or flags[0]
        and flags[1]
        or flags[2]
        and not flags[1]
    ):
        raise ValueError("Invalid care experience qualification flags")
    encounter = (
        None
        if row["encounter_id"] is None
        else integer_value(
            row["encounter_id"],
            minimum=1,
            maximum=2**63 - 2,
            context="care encounter link",
        )
    )
    if encounter is not None and (
        encounter not in encounters
        or not encounters[encounter].started_at
        <= at
        <= encounters[encounter].last_activity_at
    ):
        raise ValueError("Care experience lacks its original encounter")
    wish = (
        None
        if row["wish_instance_id"] is None
        else integer_value(
            row["wish_instance_id"],
            minimum=1,
            maximum=2**63 - 2,
            context="care experience original wish",
        )
    )
    return CareExperience(
        _token(row["receipt_id"]),
        at,
        activity,
        outcome,
        area,
        kind,
        target,
        encounter,
        wish,
        pleasant=row["pleasant"],
        upsetting=row["upsetting"],
        boundary_violated=row["boundary_violated"],
        object_id=object_id,
    )


def decode_care_evidence(
    raw: Any, baseline: float, elapsed: float
) -> CareEvidenceState:
    row = object_fields(
        raw,
        (
            "version",
            "baseline",
            "next_encounter_id",
            "encounters",
            "experiences",
            "progress",
        ),
        context="care evidence",
        optional=("next_experience_id",),
    )
    integer_value(row["version"], minimum=1, maximum=1, context="care evidence version")
    start = number_value(
        row["baseline"],
        minimum=baseline,
        maximum=elapsed,
        context="reliable care evidence baseline",
    )
    next_id = integer_value(
        row["next_encounter_id"],
        minimum=1,
        maximum=2**63 - 1,
        context="next care encounter identity",
    )
    encounters: dict[int, CareEncounter] = {}
    previous = start
    for raw_encounter in _rows(row["encounters"], MAX_CARE_ENCOUNTERS):
        value = object_fields(
            raw_encounter,
            (
                "instance_id",
                "started_at",
                "last_activity_at",
            ),
            context="care encounter",
        )
        identity = integer_value(
            value["instance_id"],
            minimum=1,
            maximum=next_id - 1,
            context="care encounter identity",
        )
        at = number_value(
            value["started_at"],
            minimum=previous,
            maximum=elapsed,
            context="care encounter beginning",
        )
        last = number_value(
            value["last_activity_at"],
            minimum=at,
            maximum=elapsed,
            context="care encounter last activity",
        )
        if identity in encounters:
            raise ValueError("Duplicate care encounter")
        encounters[identity] = CareEncounter(identity, at, last)
        previous = at
    experiences = []
    receipts: set[str] = set()
    previous = start
    for value in _rows(row["experiences"], MAX_CARE_EXPERIENCES):
        experience = _experience(value, previous, elapsed, encounters)
        if experience.receipt_id in receipts:
            raise ValueError("Duplicate semantic care receipt")
        experiences.append(experience)
        receipts.add(experience.receipt_id)
        previous = experience.occurred_at
    progress = []
    families: set[MoodletId] = set()
    family_count = sum(d.group == MoodletGroup.LONG_TERM
                       for d in MOODLET_CATALOG.definitions.values())
    for raw_progress in _rows(row["progress"], family_count):
        value = object_fields(
            raw_progress,
            (
                "definition_id",
                "period_start",
                "processed_until",
                "last_accounted_at",
                "awake_contact_gap_seconds",
            ),
            context="long-term progress",
            optional=("longest_awake_contact_gap_seconds",),
        )
        family = enum_value(
            value["definition_id"], MoodletId, context="long-term family"
        )
        if (
            family in families
            or MOODLET_CATALOG.definitions[family].group != MoodletGroup.LONG_TERM
        ):
            raise ValueError("Duplicate or ineligible long-term processing cursor")
        period = number_value(
            value["period_start"],
            minimum=start,
            maximum=elapsed,
            context="long-term period beginning",
        )
        processed = number_value(
            value["processed_until"],
            minimum=start,
            maximum=period,
            context="long-term fully processed endpoint",
        )
        accounted = number_value(
            value["last_accounted_at"],
            minimum=period,
            maximum=elapsed,
            context="long-term accounted time",
        )
        gap = number_value(
            value["awake_contact_gap_seconds"],
            minimum=0,
            maximum=accounted - start,
            context="long-term awake gap",
        )
        longest = number_value(
            value.get("longest_awake_contact_gap_seconds", gap), minimum=0,
            maximum=accounted - start, context="long-term longest awake gap",
        )
        progress.append(LongTermProgress(
            family, period, processed, accounted, gap, longest,
        ))
        families.add(family)
    return CareEvidenceState(
        start, next_id, tuple(encounters.values()), tuple(experiences), tuple(progress),
        integer_value(row.get("next_experience_id", 1), minimum=1,
                      maximum=2**63 - 1, context="next care experience identity"),
    )


def encode_care_evidence(state: CareEvidenceState) -> dict[str, Any]:
    return dict(
        version=1,
        baseline=state.baseline,
        next_encounter_id=state.next_encounter_id,
        next_experience_id=state.next_experience_id,
        encounters=[asdict(e) for e in state.encounters],
        experiences=[asdict(e) for e in state.experiences],
        progress=[asdict(p) for p in state.progress],
    )
