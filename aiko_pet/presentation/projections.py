"""Presentation-only projections of semantic pet and workload evidence."""

from __future__ import annotations

from ..personality.adaptive_models import Behaviour
from ..application.read_snapshot import PetReadSnapshot
from ..personality.catalog import EMOTION_LABELS
from ..pet.routine import TimeContext
from ..telemetry import ComputerSnapshot
from .contracts import HoverSnapshot, StatusSnapshot
from .text_de import (
    describe_workload, format_day_label, format_feed_label,
    format_mood_hint, format_percent, format_schedule_line,
)


def project_hover(
    pet: PetReadSnapshot,
    context: TimeContext,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
) -> HoverSnapshot:
    """Render the hover text without reading or mutating a pet aggregate."""
    if observe_computer:
        hardware = (
            f"MEIN RECHNER   CPU {format_percent(computer.cpu)}"
            f"   ·   GPU {format_percent(computer.gpu)}"
            f"   ·   RAM {format_percent(computer.ram)}"
        )
        workload = describe_workload(computer)
    else:
        hardware = "Rechnerbeobachtung deaktiviert"
        workload = ""
    return HoverSnapshot(
        header=f"{format_day_label(context)}   ↔ Ziehen",
        sleep_label="Wecken" if pet.sleeping else "Schlafen",
        feed_label=format_feed_label(pet, context),
        needs=pet.needs,
        friendship_level=pet.friendship_level,
        hardware_line=hardware,
        workload_line=workload,
    )


def project_status(
    pet: PetReadSnapshot,
    context: TimeContext,
    emotion: str,
    situation: Behaviour | None,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
) -> StatusSnapshot:
    """Format the current status for German desktop views only."""
    if observe_computer:
        hardware = (
            f"CPU {format_percent(computer.cpu)}  ·  "
            f"GPU {format_percent(computer.gpu)}  ·  "
            f"RAM {format_percent(computer.ram)}"
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
        today=format_day_label(context),
        next_event=format_schedule_line(context),
        hint=format_mood_hint(pet, context),
        emotion=f"Stimmung: {EMOTION_LABELS[emotion]}",
        sleep_label="Wecken" if pet.sleeping else "Schlafen",
        hardware_line=hardware,
        activity_line=activity,
        needs=pet.needs,
        friendship_level=pet.friendship_level,
    )
