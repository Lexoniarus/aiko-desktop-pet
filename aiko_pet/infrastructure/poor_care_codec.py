"""Optional emotional-processing watermarks inside the existing Moodlet save."""

from dataclasses import asdict
from typing import Any

from ..pet.balance import BALANCE
from ..pet.catalog_validation import integer_value, number_value, object_fields
from ..pet.friendship_history import NEED_NAMES
from ..pet.moodlets import PoorCareCursor, PoorCareEvidence
from ..pet.need_exposure import ExposureMark


def _mark(raw: Any, baseline: float, elapsed: float) -> ExposureMark:
    row = object_fields(raw, ("at", "critical", "zero"), context="exposure mark")
    at = number_value(row["at"], minimum=baseline, maximum=elapsed,
                      context="exposure mark time")
    size = BALANCE.number("friendship", "history_bucket_seconds")
    critical = number_value(row["critical"], minimum=0, maximum=size,
                            context="accounted critical minute")
    zero = number_value(row["zero"], minimum=0, maximum=critical,
                        context="accounted zero minute")
    return ExposureMark(at, critical, zero)


def decode_poor_care(raw: Any, baseline: float, elapsed: float) -> PoorCareEvidence:
    row = object_fields(raw, ("baseline", "needs"), context="poor-care evidence")
    start = number_value(row["baseline"], minimum=baseline, maximum=elapsed,
                         context="poor-care baseline")
    needs = object_fields(row["needs"], NEED_NAMES, context="poor-care cursors")
    cursors = []
    for name in NEED_NAMES:
        cursor = object_fields(needs[name], (
            "accounted", "handled", "handled_level", "exposed",
        ), context="poor-care cursor")
        accounted = _mark(cursor["accounted"], start, elapsed)
        handled = _mark(cursor["handled"], accounted.at, elapsed)
        level = integer_value(cursor["handled_level"], minimum=0, maximum=3,
                              context="handled poor-care level")
        if type(cursor["exposed"]) is not bool:
            raise ValueError("Exposure status must be a boolean")
        if level == 0 and handled != accounted:
            raise ValueError("Unqualified exposure cannot claim a handled threshold")
        cursors.append(PoorCareCursor(accounted, handled, level, cursor["exposed"]))
    return PoorCareEvidence(start, tuple(cursors))


def encode_poor_care(evidence: PoorCareEvidence) -> dict[str, Any]:
    return dict(baseline=evidence.baseline, needs={
        name: asdict(cursor)
        for name, cursor in zip(NEED_NAMES, evidence.needs, strict=True)
    })
