"""German presentation wording for the existing Aiko desktop interface.

The application publishes values and semantic hint keys, not translated
sentences. Status wording is owned by this view-model module.
"""

from __future__ import annotations

from ...application.read_snapshot import PetReadSnapshot
from ...pet.routine import MEAL_NAMES, WEEKDAYS, TimeContext
from ...pet.status_hints import MoodHint, choose_mood_hint
from ...telemetry import ComputerSnapshot, workload_intensity


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


_MOOD_HINT_TEXT = {
    MoodHint.SLEEP_NIGHT: "Aiko schläft gerade ... gute Nacht.",
    MoodHint.SLEEP_REST: "Aiko ruht sich aus.",
    MoodHint.HUNGRY: "Ein kleiner Snack wäre schön ...",
    MoodHint.TIRED: "Ich könnte etwas Schlaf gebrauchen.",
    MoodHint.LONELY: "...Etwas Gesellschaft wäre gerade schön.",
    MoodHint.NEEDS_AFFECTION: "...Eine kleine Geste wäre gerade schön.",
    MoodHint.BORED: "Mir ist irgendwie langweilig ...",
    MoodHint.WEEKEND: "Heute geht alles etwas langsamer. Gut so.",
    MoodHint.LATE_NIGHT: "Es ist schon spät ...",
    MoodHint.EVENING: "Endlich ein gemütlicher Abend.",
    MoodHint.GOOD_DAY: "Heute ist ein guter Tag.",
    MoodHint.CONTENT: "... Ich bin gern hier.",
}


def mood_hint_text(hint: MoodHint, context: TimeContext | None = None) -> str:
    """Translate an already selected semantic hint without choosing one."""
    if hint is MoodHint.MEAL_TIME:
        if context is None or context.meal is None:
            raise ValueError("Meal-time text needs a meal context")
        return f"Es wäre Zeit für {MEAL_NAMES[context.meal].lower()}."
    return _MOOD_HINT_TEXT[hint]


def format_mood_hint(
    pet: PetReadSnapshot, context: TimeContext | None = None,
) -> str:
    """Format the shared pet-owned hint without duplicating its rules."""
    return mood_hint_text(choose_mood_hint(pet, context), context)


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
