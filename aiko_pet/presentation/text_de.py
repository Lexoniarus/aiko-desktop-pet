"""German presentation wording for the existing Aiko desktop interface.

The application publishes values and event keys, not translated sentences.
Legacy PetState/TimeContext helpers retain their original public API.
"""

from __future__ import annotations

from ..application.read_snapshot import PetReadSnapshot
from ..pet.routine import MEAL_NAMES, WEEKDAYS, TimeContext
from ..telemetry import ComputerSnapshot, workload_intensity


def format_day_label(context: TimeContext) -> str:
    return (
        f"{WEEKDAYS[context.local.weekday()]} · "
        f"{context.local:%H:%M} · {context.activity}"
    )


def format_schedule_line(context: TimeContext) -> str:
    return f"Danach: {context.next_activity} um {context.next_time}"


def format_feed_label(pet: PetReadSnapshot, context: TimeContext) -> str:
    if context.meal and (
        context.day_key != pet.meals_date
        or context.meal not in pet.meals_today
    ):
        return MEAL_NAMES[context.meal]
    return "Snack"


def format_mood_hint(
    pet: PetReadSnapshot, context: TimeContext | None = None,
) -> str:
    """Preserve every original hint and its exact priority."""
    if pet.sleeping:
        return (
            "Aiko schläft gerade ... gute Nacht."
            if context and context.night
            else "Aiko ruht sich aus."
        )
    if pet.satiety < 20:
        return "Ein kleiner Snack wäre schön ..."
    if pet.energy < 20:
        return "Ich könnte etwas Schlaf gebrauchen."
    if pet.social < 20:
        return "...Etwas Gesellschaft wäre gerade schön."
    if pet.affection < 20:
        return "...Eine kleine Geste wäre gerade schön."
    if pet.fun < 20:
        return "Mir ist irgendwie langweilig ..."
    if context is not None:
        if context.meal and context.meal not in pet.meals_today:
            return f"Es wäre Zeit für {MEAL_NAMES[context.meal].lower()}."
        if context.weekend:
            return "Heute geht alles etwas langsamer. Gut so."
        if context.night:
            return "Es ist schon spät ..."
        if context.period == "evening":
            return "Endlich ein gemütlicher Abend."
    if min(
        pet.satiety, pet.mood, pet.energy, pet.social, pet.affection,
    ) > 85:
        return "Heute ist ein guter Tag."
    return "... Ich bin gern hier."


def format_percent(number: float | None) -> str:
    return "–" if number is None else f"{max(0, min(100, round(number)))} %"


def describe_workload(snapshot: ComputerSnapshot) -> str:
    """Aiko describes observed effort, not fabricated applications."""
    effort = workload_intensity(snapshot)
    if snapshot.measured_at <= 0 or effort is None:
        return "Ich orientiere mich noch ..."
    if effort >= 0.9:
        return "Ich bin gerade voll konzentriert."
    if effort >= 0.7:
        return "Ich habe ordentlich zu tun."
    if effort >= 0.36:
        return "Ich bin beschäftigt."
    return "Ich habe gerade etwas Ruhe."
