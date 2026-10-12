"""Pure context-specific event selection for mouse clicks on Aiko.

The catalogue provides text; this module selects which authored event applies
without mutating the pet, click history or the desktop presentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .adaptive import Behaviour
from .domain import PetState
from .routine import TimeContext

ClickButton = Literal["left", "right"]


@dataclass(frozen=True)
class ClickDecision:
    """Selected catalogue event and the previous irritation side effect."""

    event: str | None
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
    cheerful = state.mood >= 82 and state.energy >= 45 and not busy
    withdrawn = state.mood <= 28 and not busy
    tired = state.energy <= 26 or (
        situation is not None and situation.strain >= 72
    )

    if busy:
        if click_count <= 2:
            event = "click_during_work"
        elif click_count <= 4:
            event = "click_work_repeat"
        elif click_count <= 6:
            event = "click_work_boundary"
        elif click_count == 7:
            event = "click_last_word"
        else:
            return ClickDecision(None)
    elif click_count == 1 and recovering:
        event = "click_after_work"
    elif click_count <= 2:
        if withdrawn:
            event = "click_withdrawn"
        elif tired:
            event = "click_sleepy"
        elif recently_petted:
            event = "click_flustered"
        elif state.social <= 23:
            event = "click_lonely"
        elif state.affection <= 23:
            event = "click_affection_low"
        elif context.night and not cheerful:
            event = "click_night"
        elif (
            state.friendship >= 72
            and state.mood >= 60
            and state.affection >= 40
        ):
            event = "click_close"
        elif (
            state.affection >= 85
            and state.friendship >= 40
            and state.mood >= 60
        ):
            event = "click_at_ease"
        elif state.friendship < 12:
            event = "click_reserved"
        else:
            event = "click_left" if button == "left" else "click_right"
    elif click_count == 3:
        event = (
            "click_notice_playful" if cheerful
            else "click_notice_withdrawn" if withdrawn
            else "click_notice"
        )
    elif click_count <= 5:
        event = (
            "click_tease" if cheerful
            else "click_withdrawn_boundary" if withdrawn
            else "click_weary" if tired
            else "rapid_click"
        )
    elif withdrawn and click_count >= 7:
        return ClickDecision(None)
    elif withdrawn and click_count == 6:
        event = "click_last_word"
    elif click_count <= 7:
        event = "click_tease_more" if cheerful else "click_boundary"
    elif click_count == 8:
        event = "click_last_word"
    else:
        return ClickDecision(None)
    return ClickDecision(
        event=event,
        irritates=click_count >= 4 and not cheerful,
    )
