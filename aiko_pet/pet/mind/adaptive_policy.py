"""Pure observed workload classification for grounded conversation context.

Sleep priorities belong only to pet/sleep.py.  No GUI, hardware polling
or persisted memory is accessed by these functions.
"""

from __future__ import annotations

from typing import Literal

from ..balance import BALANCE

ActivityMode = Literal[
    "working",
    "recovering",
    "resting",
    "present",
    "wandering",
]


def determine_activity_mode(
    *,
    effort: float | None,
    settled_work: float,
    last_session_seconds: float,
    last_work_wall: float,
    rest_seconds: float,
    present: bool | None,
    wall_time: float,
) -> ActivityMode:
    """Classify only observed effort and bounded recent activity."""
    working = effort is not None and (
        effort >= BALANCE.number("activity_modes", "working_effort_threshold")
        or settled_work >= BALANCE.number("activity_modes", "working_settled_threshold")
    )
    if working:
        return "working"
    if last_session_seconds >= BALANCE.integer(
        "activity_modes", "recovery_minimum_session_seconds"
    ) and 0 <= wall_time - last_work_wall <= BALANCE.integer(
        "activity_modes", "recovery_recent_work_seconds"
    ):
        return "recovering"
    if rest_seconds >= BALANCE.integer("activity_modes", "resting_after_seconds"):
        return "resting"
    if present is True:
        return "present"
    return "wandering"
