"""Prepare isolated SQLite fixtures; runtime callers supply their own revision.

This helper is test-only. Loading a fixture's revision here is intentional and
must never replace the desktop's last-successful-checkpoint conflict protection.
"""

from __future__ import annotations

from aiko_pet.application.session import SavedPetStore
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import SaveRevision
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.mind.object_knowledge import ObjectMemorySnapshot
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import WorldSnapshot


def save_test_session(
    store: SavedPetStore,
    pet: PetState,
    settings: PetSettings,
    *,
    adaptive: AdaptiveMemory | None = None,
    social_history: SocialContentHistory | None = None,
    world: WorldSnapshot | None = None,
    world_recovery_x: float = 0,
    object_memory: ObjectMemorySnapshot | None = None,
) -> SaveRevision:
    """Seed or explicitly replace a disposable fixture, never advance pet time."""
    loaded = store.load_session(now=pet.updated_at)
    return store.save(
        pet,
        settings,
        expected_revision=loaded.revision,
        adaptive=loaded.adaptive_memory if adaptive is None else adaptive,
        social_history=loaded.social_history
        if social_history is None
        else social_history,
        world=world,
        world_recovery_x=world_recovery_x,
        object_memory=object_memory,
    )
