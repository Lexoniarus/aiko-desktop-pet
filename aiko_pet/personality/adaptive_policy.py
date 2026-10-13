"""Pure activity classification and sleep-policy decisions for Aiko.

All thresholds mirror the existing adaptive routine.  No GUI, hardware polling
or persisted memory is accessed by these functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ActivityMode = Literal[
    "working", "recovering", "resting", "present", "wandering",
]


@dataclass(frozen=True)
class SleepOptions:
    """Decisions consumed by the existing pet lifecycle."""

    can_sleep: bool
    should_wake: bool
    can_nap: bool


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
        effort >= 0.75 or settled_work >= 0.59
    )
    if working:
        return "working"
    if (
        last_session_seconds >= 120
        and 0 <= wall_time - last_work_wall <= 180
    ):
        return "recovering"
    if rest_seconds >= 300:
        return "resting"
    if present is True:
        return "present"
    return "wandering"


def determine_sleep_options(
    *,
    mode: ActivityMode,
    energy: float,
    sleeping: bool,
    manual_sleep: bool,
    night: bool,
    effort: float | None,
    idle_seconds: float | None,
    present: bool | None,
    rest_seconds: float,
    expected_effort: float | None,
) -> SleepOptions:
    """Use measured rest, night bias and existing manual-sleep overrides."""
    working = mode == "working"
    quiet_enough = (
        not working
        and (effort is None or effort < 0.38)
        and (idle_seconds is None or idle_seconds >= 180)
    )
    can_sleep = (
        (night and not working and (quiet_enough or energy <= 17))
        or (energy <= 23 and rest_seconds >= 1800)
    )
    should_wake = (
        not manual_sleep and sleeping
        and (working or (not night and present is True))
    )
    can_nap = (
        not night and present is False and not working
        and rest_seconds >= 900
        and (
            energy <= 18
            or (
                energy <= 35 and expected_effort is not None
                and expected_effort < 0.32
            )
        )
    )
    return SleepOptions(
        can_sleep=can_sleep, should_wake=should_wake, can_nap=can_nap,
    )
