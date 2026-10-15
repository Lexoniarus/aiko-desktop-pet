"""Choose moderate care requests without changing needs or urgent emotions."""

from __future__ import annotations

from ..pet.balance import BALANCE

from ..pet.state import PetState


def choose_care_request(state: PetState) -> str | None:
    """Lowest need wins; tuple order provides the explicit tie-break priority."""
    if state.sleeping:
        return None
    event, value = min(
        (
            ("care_request_feed", state.satiety),
            ("care_request_talk", state.social),
            ("care_request_pet", state.affection),
            ("care_request_play", state.fun),
        ),
        key=lambda item: item[1],
    )
    return (
        event if value <= BALANCE.integer("care_requests", "need_threshold") else None
    )
