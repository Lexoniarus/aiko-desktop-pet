"""Presentation-only projections of semantic pet and workload evidence."""

from __future__ import annotations

from ...application.object_status import ObjectStatusSnapshot
from ...application.read_snapshot import PetReadSnapshot
from ...application.settings import PetSettings
from ...pet.content import GERMAN_TEXT
from ...pet.food import FOOD_CATALOG
from ...pet.mind.adaptive_models import Behaviour
from ...pet.routine import TimeContext
from ...telemetry import ComputerSnapshot
from .contracts import HoverSnapshot, SettingsSnapshot, StatusSnapshot
from .text_de import (
    describe_workload,
    format_day_label,
    format_emotion_label,
    format_feed_label,
    format_mood_hint,
    format_percent,
    format_schedule_line,
    format_sleep_label,
    observation_disabled_text,
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
        hardware = GERMAN_TEXT.format(
            "ui.hover_hardware",
            cpu=format_percent(computer.cpu),
            gpu=format_percent(computer.gpu),
            ram=format_percent(computer.ram),
        )
        workload = describe_workload(computer)
    else:
        hardware = observation_disabled_text()
        workload = ""
    return HoverSnapshot(
        header=GERMAN_TEXT.format(
            "ui.hover_header",
            day_label=format_day_label(context),
        ),
        sleep_label=format_sleep_label(pet.sleeping),
        feed_label=format_feed_label(pet, context),
        needs=pet.needs,
        friendship_level=pet.friendship_level,
        hardware_line=hardware,
        workload_line=workload,
        food_line=(
            GERMAN_TEXT.format(
                "ui.last_food",
                food=FOOD_CATALOG[pet.last_food_id].display_name,
                minutes=f"{pet.food_digest_minutes:.0f}",
            )
            if pet.last_food_id is not None
            else ""
        ),
    )


def project_status(
    pet: PetReadSnapshot,
    context: TimeContext,
    emotion: str,
    situation: Behaviour | None,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
    objects: ObjectStatusSnapshot = ObjectStatusSnapshot(),
) -> StatusSnapshot:
    """Format the current status for German desktop views only."""
    if observe_computer:
        hardware = GERMAN_TEXT.format(
            "ui.status_hardware",
            cpu=format_percent(computer.cpu),
            gpu=format_percent(computer.gpu),
            ram=format_percent(computer.ram),
        )
    else:
        hardware = observation_disabled_text()
    if observe_computer and situation is not None:
        descriptions = {
            "working": GERMAN_TEXT.format("activity.working"),
            "recovering": GERMAN_TEXT.format("activity.recovering"),
            "resting": GERMAN_TEXT.format("activity.resting"),
            "present": GERMAN_TEXT.format("activity.present"),
            "wandering": GERMAN_TEXT.format("activity.wandering"),
        }
        summary = descriptions.get(
            situation.mode, GERMAN_TEXT.format("activity.unknown")
        )
        if situation.expectation_confident:
            summary += GERMAN_TEXT.format("activity.familiar_suffix")
        activity = GERMAN_TEXT.format(
            "activity.summary",
            summary=summary,
            strain=f"{situation.strain:.0f}",
        )
        if situation.uptime_hours is not None:
            activity += GERMAN_TEXT.format(
                "activity.uptime_suffix",
                hours=f"{situation.uptime_hours:.1f}",
            )
    else:
        activity = GERMAN_TEXT.format("activity.learning") if observe_computer else ""
    return StatusSnapshot(
        today=format_day_label(context),
        next_event=format_schedule_line(context),
        hint=format_mood_hint(pet, context),
        emotion=format_emotion_label(emotion),
        sleep_label=format_sleep_label(pet.sleeping),
        hardware_line=hardware,
        activity_line=activity,
        needs=pet.needs,
        friendship_level=pet.friendship_level,
        objects_line=GERMAN_TEXT.format(
            "ui.object_status", desktop=str(objects.desktop), known=str(objects.known),
            assigned=str(objects.assigned), missing=str(objects.missing),
        ),
    )


def project_settings(settings: PetSettings) -> SettingsSnapshot:
    """Produce one authoritative desktop preferences view for every caller."""
    return SettingsSnapshot(
        scale=settings.scale,
        options=(
            ("always_on_top", settings.always_on_top),
            ("auto_walk", settings.auto_walk),
            ("auto_routine", settings.auto_routine),
            ("follow_cursor", settings.follow_cursor),
            ("spontaneous_talk", settings.spontaneous_talk),
            ("observe_computer", settings.observe_computer),
            ("learn_rhythm", settings.learn_rhythm),
        ),
    )
