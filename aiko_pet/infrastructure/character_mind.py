"""Choose packaged Aiko dialogue outside the generic pet mind implementation."""

from __future__ import annotations

import random

from ..pet.mind import PetMind
from ..pet.mind.catalog import CATALOGUE, DialogueBook


def make_aiko_mind(
    *, started_at: float, rng: random.Random | None = None,
) -> PetMind:
    """Inject one shared RNG and Aiko's authored catalogue into a pure mind."""
    source_rng = rng if rng is not None else random.Random()
    return PetMind(
        book=DialogueBook.from_file(CATALOGUE, rng=source_rng),
        rng=source_rng, started_at=started_at,
    )
