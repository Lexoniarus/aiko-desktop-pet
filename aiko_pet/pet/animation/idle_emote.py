"""Pure, need-dependent idle emote choice for a pet."""

from __future__ import annotations

from ..balance import BALANCE


def choose_idle_emote(
    *,
    energy: float,
    satiety: float,
    mood: float,
    affection: float,
) -> str:
    """Select the original need-dependent idle icon in priority order."""
    if energy < BALANCE.integer("idle_emotes", "tired_energy"):
        return "sleeps"
    if satiety < BALANCE.integer("idle_emotes", "hungry_satiety"):
        return "drops"
    if mood < BALANCE.integer("idle_emotes", "sad_mood"):
        return "faceSad"
    if affection < BALANCE.integer("idle_emotes", "low_affection"):
        return "heart"
    if mood > BALANCE.integer("idle_emotes", "happy_mood"):
        return "star"
    return "idea"
