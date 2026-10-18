"""Test-only PetState scenario adjustments through the checkpoint contract."""

from __future__ import annotations

from dataclasses import fields, replace
from typing import Any

from aiko_pet.pet.mind.object_attention import AttentionMode, ObjectAttention
from aiko_pet.pet.state import PetState
from aiko_pet.pet.state_values import PetValues

_NAMES = frozenset(field.name for field in fields(PetValues))


def set_test_pet_values(state: PetState, **changes: Any) -> None:
    """Adjust a fixture in place without adding production attribute setters."""
    unexpected = set(changes) - _NAMES
    if unexpected:
        raise ValueError(f"Unknown PetState scenario fields: {sorted(unexpected)}")
    for name in ("care_types_today", "meals_today"):
        if name in changes:
            changes[name] = tuple(changes[name])
    if "care_last_rewards" in changes:
        rewards = changes["care_last_rewards"]
        changes["care_last_rewards"] = tuple(rewards.items())
    state.restore_checkpoint(replace(state.capture_checkpoint(), **changes))


def object_test_attention(
    x: float, *, width: float, height: float = 0, attentive: bool = True,
    direction: tuple[float, float] = (1, 0), mode: AttentionMode = "survey",
) -> ObjectAttention:
    """An explicit right-facing sensor fixture; callers can select another look."""
    return ObjectAttention(mode if attentive else "unavailable", direction,
                           origin=(x, height), width=width)
