"""Pure, need-dependent idle emote choice for a pet."""

from __future__ import annotations


def choose_idle_emote(
    *, energy: float, satiety: float, mood: float, affection: float,
) -> str:
    """Select the original need-dependent idle icon in priority order."""
    if energy < 20:
        return "sleeps"
    if satiety < 18:
        return "drops"
    if mood < 18:
        return "faceSad"
    if affection < 18:
        return "heart"
    if mood > 88:
        return "star"
    return "idea"
