"""Presentation-only projections of semantic pet and workload evidence."""

from __future__ import annotations

from ...application.object_status import ObjectStatusSnapshot
from ...application.read_snapshot import PetReadSnapshot
from ...application.settings import PetSettings
from ...pet.content import GERMAN_TEXT
from ...pet.food import FOOD_CATALOG
from ...pet.mind.adaptive_models import Behaviour
from ...pet.routine import TimeContext
from ...pet.wishes import WishTargetKind, wish_text_key
from ...telemetry import ComputerSnapshot
from .contracts import (
    EmotionalSnapshot,
    HoverSnapshot,
    MoodletView,
    SettingsSnapshot,
    StatusSnapshot,
    WishView,
)
from .emotional_text import duration_text
from .text_de import (
    describe_workload,
    format_day_label,
    format_emotional_state,
    format_feed_label,
    format_percent,
    format_schedule_line,
    format_sleep_label,
    format_status_hint,
    observation_disabled_text,
)


def _status_values(pet: PetReadSnapshot) -> tuple[tuple[str, float], ...]:
    """Presentation order for care, mood and relationship, not a need model."""
    needs = pet.needs
    return (
        ("satiety", needs.satiety),
        ("mood", pet.mood),
        ("fun", needs.fun),
        ("energy", needs.energy),
        ("social", needs.social),
        ("affection", needs.affection),
        ("friendship", pet.friendship),
    )


def _emotional_snapshot(pet: PetReadSnapshot) -> EmotionalSnapshot:
    wishes = []
    for wish in pet.wishes:
        label = GERMAN_TEXT.format(
            wish_text_key(wish.definition_id, wish.goal, "label"),
        )
        target = (
            FOOD_CATALOG[wish.target_id].display_name
            if wish.target_kind == WishTargetKind.FOOD
            else GERMAN_TEXT.format(f"game.name.{wish.target_id}")
            if wish.target_kind == WishTargetKind.GAME
            else label
        )
        wishes.append(
            WishView(
                wish,
                label,
                GERMAN_TEXT.format(wish_text_key(wish.definition_id, wish.goal,
                                                "description")),
                target,
                (
                    GERMAN_TEXT.format(f"wish.restriction.{wish.restriction}")
                    if wish.restriction is not None
                    else ""
                ),
            )
        )
    return EmotionalSnapshot(
        pet.emotions,
        format_emotional_state(pet.emotions.primary),
        pet.need_conditions,
        tuple(
            MoodletView(
                m,
                GERMAN_TEXT.format(f"moodlet.{m.definition_id}.label"),
                GERMAN_TEXT.format(f"moodlet.{m.definition_id}.description"),
            )
            for m in pet.moodlets
        ),
        tuple(wishes),
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
        status_values=_status_values(pet),
        friendship_level=pet.friendship_level,
        emotional=_emotional_snapshot(pet),
        wellbeing_line=GERMAN_TEXT.format(
            "vn.wellbeing", target=f"{pet.mood_target:.0f}"
        ),
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
        hint=format_status_hint(pet, context),
        sleep_label=format_sleep_label(pet.sleeping),
        hardware_line=hardware,
        activity_line=activity,
        status_values=_status_values(pet),
        friendship_level=pet.friendship_level,
        emotional=_emotional_snapshot(pet),
        wellbeing_line=GERMAN_TEXT.format(
            "vn.wellbeing", target=f"{pet.mood_target:.0f}"
        ),
        relationship_line=GERMAN_TEXT.format(
            "vn.relationship",
            stage=GERMAN_TEXT.format(f"vn.stage.{pet.friendship_stage}"),
            level=str(pet.friendship_level),
        ),
        sleep_context_line=GERMAN_TEXT.format(f"vn.sleep.{pet.sleep_reason}"),
        contact_line=(
            GERMAN_TEXT.format(
                "vn.contact_known", time=duration_text(pet.contact_absence_seconds)
            )
            if pet.contact_absence_seconds is not None
            else GERMAN_TEXT.format("vn.contact_unknown")
        ),
        objects_line=GERMAN_TEXT.format(
            "ui.object_status",
            desktop=str(objects.desktop),
            undiscovered=str(objects.undiscovered),
            unidentified=str(objects.unidentified),
            unresolved=str(objects.unresolved),
            known=str(objects.known),
            assigned=str(objects.assigned),
            missing=str(objects.missing),
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
            ("online_social", settings.online_social),
        ),
    )
