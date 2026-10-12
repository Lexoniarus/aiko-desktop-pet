"""Tamagotchi care-action rules, separate from state serialization and GUI.

Care actions mutate only the supplied pet state and return the existing
German fallback text. AikoMind separately selects situational dialogue.
"""

from __future__ import annotations

import time
from typing import Protocol

from .friendship import CARE_PRIMARY_NEED
from .routine import MEAL_NAMES, TimeContext, context_at
from .value_rules import clamp_need_value


class CareState(Protocol):
    """Minimal mutable pet-state interface needed by care actions."""

    sleeping: bool
    sleep_origin: str
    auto_sleep_night: str
    nap_until: float
    energy: float
    satiety: float
    mood: float
    social: float
    affection: float
    meals_today: list[str]

    def _roll_meals(self, context: TimeContext) -> None: ...

    def _credit_friendship(
        self, action: str, stamp: float, need_before: float,
    ) -> None: ...


def apply_care_action(
    state: CareState, action: str, *, now: float | None = None,
) -> str:
    """Apply one validated care action without changing reward/timing rules."""
    stamp = time.time() if now is None else now
    if action == "sleep":
        return _toggle_manual_sleep(state, stamp)
    if action not in {"feed", "play", "pet", "talk", "energy_drink"}:
        raise ValueError(f"Unknown action: {action}")
    if action == "play" and state.energy < 8:
        return "Ich bin gerade zu müde zum Spielen."
    if action == "energy_drink" and state.energy >= 100:
        return "Ich bin schon voll. Mehr passt gerade nicht rein."

    _wake_for_care(state, stamp)

    if action == "energy_drink":
        state.energy = clamp_need_value(state.energy + 10.0)
        return "...Oh. Das hat geholfen."

    need_before = getattr(state, CARE_PRIMARY_NEED[action])
    if action == "talk":
        return _apply_conversation(state, stamp, need_before)
    if action == "feed":
        return _apply_feeding(state, stamp, need_before)
    if action == "play":
        return _apply_playtime(state, stamp, need_before)
    return _apply_petting(state, stamp, need_before)


def _toggle_manual_sleep(state: CareState, stamp: float) -> str:
    state.sleeping = not state.sleeping
    state.sleep_origin = "manual" if state.sleeping else ""
    if not state.sleeping and context_at(stamp).night:
        state.auto_sleep_night = context_at(stamp).night_key
    return "Zzz ... gute Nacht." if state.sleeping else "Oh ... schon Morgen?"


def _wake_for_care(state: CareState, stamp: float) -> None:
    if not state.sleeping:
        return
    state.sleeping = False
    state.sleep_origin = ""
    state.nap_until = 0.0
    context = context_at(stamp)
    if context.night:
        # User-initiated care must not restart automatic sleep one tick later.
        state.auto_sleep_night = context.night_key


def _apply_conversation(state: CareState, stamp: float, need_before: float) -> str:
    state.social = clamp_need_value(state.social + 26)
    state.mood = clamp_need_value(state.mood + 5)
    state.energy = clamp_need_value(state.energy - 1)
    state._credit_friendship("talk", stamp, need_before)
    return "...Du möchtest reden? Ich höre zu."


def _apply_feeding(state: CareState, stamp: float, need_before: float) -> str:
    context = context_at(stamp)
    state._roll_meals(context)
    state.satiety = clamp_need_value(state.satiety + 27)
    state.social = clamp_need_value(state.social + 1)
    state._credit_friendship("feed", stamp, need_before)
    if context.meal is not None and context.meal not in state.meals_today:
        state.meals_today.append(context.meal)
        state.mood = clamp_need_value(state.mood + 5)
        return f"Danke für das {MEAL_NAMES[context.meal].lower()}!"
    state.mood = clamp_need_value(state.mood + 3)
    return "Mhm ... ein kleiner Snack!"


def _apply_playtime(state: CareState, stamp: float, need_before: float) -> str:
    state.mood = clamp_need_value(state.mood + 23)
    state.energy = clamp_need_value(state.energy - 9)
    state.satiety = clamp_need_value(state.satiety - 4)
    state.social = clamp_need_value(state.social + 12)
    state._credit_friendship("play", stamp, need_before)
    return "Heh ... das war gut!"


def _apply_petting(state: CareState, stamp: float, need_before: float) -> str:
    state.affection = clamp_need_value(state.affection + 25)
    state.mood = clamp_need_value(state.mood + 6)
    state.social = clamp_need_value(state.social + 2)
    state._credit_friendship("pet", stamp, need_before)
    return "... Das ist angenehm."
