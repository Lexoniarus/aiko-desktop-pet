"""German presentation wording for the existing Aiko desktop interface.

The application publishes values and semantic hint keys, not translated
sentences. Status wording is owned by this view-model module.
"""

from __future__ import annotations

from ...pet.balance import BALANCE

from ...application.read_snapshot import PetReadSnapshot
from ...pet.content import GERMAN_TEXT
from ...pet.routine import MEAL_NAMES, TimeContext, due_meal
from ...pet.status_hints import MoodHint, choose_mood_hint
from ...telemetry import ComputerSnapshot, workload_intensity


WEEKDAYS = tuple(GERMAN_TEXT.format(f"weekday.{i}") for i in range(7))


def format_day_label(context: TimeContext) -> str:
    return GERMAN_TEXT.format(
        "ui.day_label",
        weekday=WEEKDAYS[context.local.weekday()],
        time=f"{context.local:%H:%M}",
        activity=context.activity,
    )


def format_schedule_line(context: TimeContext) -> str:
    return GERMAN_TEXT.format(
        "ui.schedule_next",
        activity=context.next_activity,
        time=context.next_time,
    )


def format_emotion_label(emotion: str) -> str:
    """Render the current semantic PetMind emotion without domain UI copy."""
    return GERMAN_TEXT.format(
        "ui.emotion_label",
        emotion=GERMAN_TEXT.format(f"emotion.{emotion}"),
    )


def format_sleep_label(sleeping: bool) -> str:
    """Share the sleep button label across hover and status projections."""
    return GERMAN_TEXT.format("ui.sleep_wake" if sleeping else "ui.sleep_start")


def observation_disabled_text() -> str:
    """Share one localized observation-off label between both views."""
    return GERMAN_TEXT.format("ui.observation_disabled")


def format_feed_label(pet: PetReadSnapshot, context: TimeContext) -> str:
    """Translate the canonical due-meal decision to the existing UI label."""
    meal = due_meal(
        context,
        meals_date=pet.meals_date,
        meals_today=pet.meals_today,
    )
    return MEAL_NAMES[meal] if meal is not None else GERMAN_TEXT.format("ui.snack")


def mood_hint_text(hint: MoodHint, context: TimeContext | None = None) -> str:
    """Render a semantic status hint using validated German JSON copy."""
    if hint is MoodHint.MEAL_TIME:
        if context is None or context.meal is None:
            raise ValueError("Meal-time text needs a meal context")
        return GERMAN_TEXT.format(
            "mood.meal_time",
            meal=MEAL_NAMES[context.meal].lower(),
        )
    return GERMAN_TEXT.format(f"mood.{hint.value}")


def format_mood_hint(
    pet: PetReadSnapshot,
    context: TimeContext | None = None,
) -> str:
    """Format the shared pet-owned hint without duplicating its rules."""
    return mood_hint_text(choose_mood_hint(pet, context), context)


def format_percent(number: float | None) -> str:
    return (
        GERMAN_TEXT.format("ui.percent_missing")
        if number is None
        else GERMAN_TEXT.format(
            "ui.percent",
            percent=str(max(0, min(100, round(number)))),
        )
    )


def describe_workload(snapshot: ComputerSnapshot) -> str:
    """Aiko describes observed effort, not fabricated applications."""
    effort = workload_intensity(snapshot)
    if snapshot.measured_at <= 0 or effort is None:
        return GERMAN_TEXT.format("workload.unobserved")
    if effort >= BALANCE.number("workload_copy", "high_effort"):
        return GERMAN_TEXT.format("workload.high")
    if effort >= BALANCE.number("workload_copy", "medium_effort"):
        return GERMAN_TEXT.format("workload.medium")
    if effort >= BALANCE.number("workload_copy", "busy_effort"):
        return GERMAN_TEXT.format("workload.busy")
    return GERMAN_TEXT.format("workload.calm")
