"""Pure context-specific event selection for mouse clicks on Aiko.

The catalogue provides text; this module selects which authored event applies
without mutating the pet, click history or the desktop presentation.
"""

from __future__ import annotations

from ..balance import BALANCE

from dataclasses import dataclass
from typing import Literal

from .adaptive_models import Behaviour
from ..state import PetState
from ..routine import TimeContext

ClickButton = Literal["left", "right"]
ClickEvent = Literal[
    "sleep_click",
    "click_during_work",
    "click_work_repeat",
    "click_work_boundary",
    "click_last_word",
    "click_after_work",
    "click_withdrawn",
    "click_sleepy",
    "click_flustered",
    "click_lonely",
    "click_affection_low",
    "click_night",
    "click_close",
    "click_at_ease",
    "click_reserved",
    "click_left",
    "click_right",
    "click_notice_playful",
    "click_notice_withdrawn",
    "click_notice",
    "click_tease",
    "click_withdrawn_boundary",
    "click_weary",
    "rapid_click",
    "click_tease_more",
    "click_boundary",
]


@dataclass(frozen=True)
class ClickDecision:
    """Selected catalogue event and the previous irritation side effect."""

    event: ClickEvent | None
    irritates: bool = False


def choose_click_reaction(
    *,
    button: ClickButton,
    click_count: int,
    state: PetState,
    context: TimeContext,
    situation: Behaviour | None,
    recovering: bool,
    recently_petted: bool,
) -> ClickDecision:
    """Match the established click escalation, mood and work boundaries."""
    if button not in ("left", "right"):
        raise ValueError("Unknown mouse button")
    if state.sleeping:
        return ClickDecision("sleep_click")
    busy = situation is not None and situation.focused
    cheerful = (
        state.mood >= BALANCE.integer("click", "cheerful_mood")
        and state.energy >= BALANCE.integer("click", "cheerful_energy")
        and not busy
    )
    withdrawn = state.mood <= BALANCE.integer("click", "withdrawn_mood") and not busy
    tired = state.energy <= BALANCE.integer("click", "tired_energy") or (
        situation is not None
        and situation.strain >= BALANCE.integer("click", "tired_strain")
    )
    event: ClickEvent

    if busy:
        if click_count <= BALANCE.integer("click", "initial_click_count"):
            event = "click_during_work"
        elif click_count <= BALANCE.integer("click", "work_repeat_click_count"):
            event = "click_work_repeat"
        elif click_count <= BALANCE.integer("click", "work_boundary_click_count"):
            event = "click_work_boundary"
        elif click_count == BALANCE.integer("click", "work_last_word_click_count"):
            event = "click_last_word"
        else:
            return ClickDecision(None)
    elif click_count == 1 and recovering:
        event = "click_after_work"
    elif click_count <= BALANCE.integer("click", "initial_click_count"):
        if withdrawn:
            event = "click_withdrawn"
        elif tired:
            event = "click_sleepy"
        elif recently_petted:
            event = "click_flustered"
        elif state.social <= BALANCE.integer("click", "lonely_social"):
            event = "click_lonely"
        elif state.affection <= BALANCE.integer("click", "low_affection"):
            event = "click_affection_low"
        elif context.night and not cheerful:
            event = "click_night"
        elif (
            state.friendship >= BALANCE.integer("click", "close_friendship")
            and state.mood >= BALANCE.integer("click", "close_mood")
            and state.affection >= BALANCE.integer("click", "close_affection")
        ):
            event = "click_close"
        elif (
            state.affection >= BALANCE.integer("click", "at_ease_affection")
            and state.friendship >= BALANCE.integer("click", "at_ease_friendship")
            and state.mood >= BALANCE.integer("click", "close_mood")
        ):
            event = "click_at_ease"
        elif state.friendship < BALANCE.integer("click", "reserved_friendship"):
            event = "click_reserved"
        else:
            event = "click_left" if button == "left" else "click_right"
    elif click_count == BALANCE.integer("click", "notice_click_count"):
        event = (
            "click_notice_playful"
            if cheerful
            else "click_notice_withdrawn"
            if withdrawn
            else "click_notice"
        )
    elif click_count <= BALANCE.integer("click", "tease_click_count"):
        event = (
            "click_tease"
            if cheerful
            else "click_withdrawn_boundary"
            if withdrawn
            else "click_weary"
            if tired
            else "rapid_click"
        )
    elif withdrawn and click_count >= BALANCE.integer(
        "click", "withdrawn_boundary_click_count"
    ):
        return ClickDecision(None)
    elif withdrawn and click_count == BALANCE.integer(
        "click", "withdrawn_weary_click_count"
    ):
        event = "click_last_word"
    elif click_count <= BALANCE.integer("click", "tease_more_click_count"):
        event = "click_tease_more" if cheerful else "click_boundary"
    elif click_count == BALANCE.integer("click", "last_boundary_click_count"):
        event = "click_last_word"
    else:
        return ClickDecision(None)
    return ClickDecision(
        event=event,
        irritates=click_count >= BALANCE.integer("click", "irritation_click_count")
        and not cheerful,
    )
