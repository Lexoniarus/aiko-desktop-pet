"""Immutable, language-neutral pet data for application read operations."""

from __future__ import annotations

from ..pet.balance import BALANCE

from dataclasses import dataclass

from ..pet.state import PetState


@dataclass(frozen=True, slots=True)
class PetReadSnapshot:
    """Stable value copy, not a mutable reference to PetState."""

    satiety: float
    mood: float
    energy: float
    social: float
    affection: float
    friendship: float
    friendship_level: int
    sleeping: bool
    meals_date: str
    meals_today: tuple[str, ...]
    last_food_id: str | None = None
    food_digest_minutes: float = 0.0
    fun: float = BALANCE.number("initial", "fun")

    @property
    def needs(self) -> tuple[tuple[str, float], ...]:
        return (
            ("satiety", self.satiety),
            ("mood", self.mood),
            ("energy", self.energy),
            ("social", self.social),
            ("affection", self.affection),
            ("friendship", self.friendship),
        )


def snapshot_pet(state: PetState) -> PetReadSnapshot:
    """Copy a pet's current read-side values, without computing UI text."""
    return PetReadSnapshot(
        satiety=state.satiety,
        mood=state.mood,
        energy=state.energy,
        social=state.social,
        affection=state.affection,
        friendship=state.friendship,
        friendship_level=state.friendship_level,
        sleeping=state.sleeping,
        meals_date=state.meals_date,
        meals_today=tuple(state.meals_today),
        last_food_id=state.food.last_food_id,
        food_digest_minutes=state.food.remaining_digest_minutes,
        fun=state.fun,
    )
