"""Compose existing owner mappers in the caller's one snapshot transaction.

No clock, offline progression or mutable aggregate is introduced. A restored
PetState is assembled from its existing immutable checkpoint representation.
"""

from __future__ import annotations

import sqlite3
from dataclasses import replace

from ...application.session import LoadedPetData
from ...application.settings import PetSettings
from ...application.social_history import SocialContentHistory
from ...application.storage_contracts import SaveRevision
from ...pet.mind.adaptive_models import AdaptiveMemory
from ...pet.mind.object_knowledge import ObjectMemorySnapshot
from ...pet.state import PetState
from ...pet.state_values import PetValues
from ...world.contracts import ObjectDefinition, WorldSnapshot
from .adaptive_rows import read_adaptive, write_adaptive
from .moodlet_rows import read_moodlets, write_moodlets
from .pet_rows import read_pet_core, write_pet_core
from .relationship_rows import read_friendship, write_friendship
from .rows import singleton
from .settings_rows import read_settings, write_settings
from .social_rows import read_social_history, write_social_history
from .wish_rows import read_wishes, write_wishes
from .world_rows import read_world_memory, write_world_memory


def write_session_rows(
    connection: sqlite3.Connection,
    values: PetValues,
    settings: PetSettings,
    *,
    adaptive: AdaptiveMemory,
    social_history: SocialContentHistory,
    world: WorldSnapshot | None,
    object_memory: ObjectMemorySnapshot | None,
    world_recovery_x: float,
) -> None:
    """Time/revision were written by the transaction owner; no mapper commits."""
    write_pet_core(connection, values)
    write_settings(connection, settings)
    write_friendship(connection, values.relationship)
    write_moodlets(connection, values.moodlets)
    write_wishes(connection, values.wishes)
    write_world_memory(connection, world, object_memory, recovery_x=world_recovery_x)
    write_adaptive(connection, adaptive)
    write_social_history(connection, social_history)


def read_session_rows(
    connection: sqlite3.Connection,
    definitions: tuple[ObjectDefinition, ...],
) -> LoadedPetData:
    anchor = singleton(connection, "save_state")
    revision = SaveRevision(anchor["revision"])
    if revision.value == 0:
        raise ValueError("Persisted checkpoint must have a positive revision")
    state = PetState(
        updated_at=anchor["updated_at"], lived_seconds=anchor["lived_seconds"]
    )
    values = read_pet_core(connection, state.capture_checkpoint())
    state.restore_checkpoint(
        replace(
            values,
            relationship=read_friendship(connection),
            moodlets=read_moodlets(connection),
            wishes=read_wishes(connection),
        )
    )
    world, memory = read_world_memory(connection, definitions)
    return LoadedPetData(
        state,
        read_settings(connection),
        read_adaptive(connection),
        True,
        world,
        memory,
        read_social_history(connection),
        revision,
    )
