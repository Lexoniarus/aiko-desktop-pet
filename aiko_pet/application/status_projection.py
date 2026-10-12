"""Turn domain state and measured activity into plain status-panel text."""

from __future__ import annotations

from ..adaptive_models import Behaviour
from ..dialogue import AikoMind, EMOTION_LABELS
from ..domain import PetState
from ..routine import TimeContext
from ..system_activity import ComputerSnapshot, percent_label
from .view_models import StatusSnapshot


def project_status(
    state: PetState,
    context: TimeContext,
    mind: AikoMind,
    situation: Behaviour | None,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
    now: float,
) -> StatusSnapshot:
    """Compute all labels before crossing the Tk presentation boundary."""
    if observe_computer:
        hardware = (
            f"CPU {percent_label(computer.cpu)}  ·  "
            f"GPU {percent_label(computer.gpu)}  ·  "
            f"RAM {percent_label(computer.ram)}"
        )
    else:
        hardware = "Rechnerbeobachtung deaktiviert"

    if observe_computer and situation is not None:
        descriptions = {
            "working": "Konzentriert bei der Arbeit",
            "recovering": "Nach der Arbeit zur Ruhe kommen",
            "resting": "Eine ruhige Pause genießen",
            "present": "Wach und aufmerksam",
            "wandering": "Zeit für mich",
        }
        summary = descriptions.get(situation.mode, "Ich bin hier")
        if situation.expectation_confident:
            summary += " · eingespielter Tagesrhythmus"
        activity = (
            f"Mein Rhythmus: {summary} · "
            f"Beanspruchung {situation.strain:.0f}/100"
        )
        if situation.uptime_hours is not None:
            activity += f" · Rechnerlaufzeit {situation.uptime_hours:.1f} h"
    else:
        activity = "Mein Rhythmus: lernt noch" if observe_computer else ""
    return StatusSnapshot(
        today=context.label,
        next_event=context.schedule_line,
        hint=state.mood_hint(context),
        emotion=f"Stimmung: {EMOTION_LABELS[mind.emotion(state, now)]}",
        sleep_label="Wecken" if state.sleeping else "Schlafen",
        hardware_line=hardware,
        activity_line=activity,
        needs=(
            ("satiety", state.satiety), ("mood", state.mood),
            ("energy", state.energy), ("social", state.social),
            ("affection", state.affection), ("friendship", state.friendship),
        ),
        friendship_level=state.friendship_level,
    )
