"""Choose packaged Aiko dialogue outside the generic pet mind implementation."""

from __future__ import annotations

import random

from ..pet.mind import PetMind
from ..pet.mind.catalog import CATALOGUE, DialogueBook


def make_aiko_mind(*, started_at: float) -> PetMind:
    """Wire one RNG into the packaged dialogue and PetMind, as before."""
    rng = random.Random()
    return PetMind(
        book=DialogueBook.from_file(CATALOGUE, rng=rng),
        rng=rng, started_at=started_at,
    )
