"""Pure activity classification and sleep-policy decisions for Aiko.

All thresholds mirror the existing adaptive routine.  No GUI, hardware polling
or persisted memory is accessed by these functions.
"""

from __future__ import annotations

from ..balance import BALANCE

from dataclasses import dataclass
from typing import Literal

ActivityMode = Literal[
    "working",
    "recovering",
    "resting",
    "present",
    "wandering",
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
        effort >= BALANCE.number("adaptive_sleep", "working_effort_threshold")
        or settled_work >= BALANCE.number("adaptive_sleep", "working_settled_threshold")
    )
    if working:
        return "working"
    if last_session_seconds >= BALANCE.integer(
        "adaptive_sleep", "recovery_minimum_session_seconds"
    ) and 0 <= wall_time - last_work_wall <= BALANCE.integer(
        "adaptive_sleep", "recovery_recent_work_seconds"
    ):
        return "recovering"
    if rest_seconds >= BALANCE.integer("adaptive_sleep", "resting_after_seconds"):
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
        and (
            effort is None
            or effort < BALANCE.number("adaptive_sleep", "quiet_maximum_effort")
        )
        and (
            idle_seconds is None
            or idle_seconds
            >= BALANCE.integer("adaptive_sleep", "quiet_minimum_idle_seconds")
        )
    )
    can_sleep = (
        night
        and not working
        and (
            quiet_enough
            or energy <= BALANCE.integer("adaptive_sleep", "night_forced_sleep_energy")
        )
    ) or (
        energy <= BALANCE.integer("adaptive_sleep", "rest_sleep_energy")
        and rest_seconds
        >= BALANCE.integer("adaptive_sleep", "rest_sleep_after_seconds")
    )
    should_wake = (
        not manual_sleep and sleeping and (working or (not night and present is True))
    )
    can_nap = (
        not night
        and present is False
        and not working
        and rest_seconds >= BALANCE.integer("adaptive_sleep", "nap_after_rest_seconds")
        and (
            energy <= BALANCE.integer("adaptive_sleep", "nap_low_energy")
            or (
                energy <= BALANCE.integer("adaptive_sleep", "nap_expected_quiet_energy")
                and expected_effort is not None
                and expected_effort
                < BALANCE.number("adaptive_sleep", "nap_expected_effort")
            )
        )
    )
    return SleepOptions(
        can_sleep=can_sleep,
        should_wake=should_wake,
        can_nap=can_nap,
    )
