"""Decode a complete supported legacy save without I/O or pet progression."""

from typing import Any

from ..application.session import LoadedPetData
from ..application.settings import PetSettings
from ..application.social_history import SocialContentHistory
from ..pet.catalog_validation import decode_json, object_fields
from ..pet.mind.adaptive_models import AdaptiveMemory
from ..world.contracts import ObjectDefinition, ObjectInteraction
from .adaptive_codec import decode_adaptive, encode_adaptive
from .legacy_pet_codec import decode_legacy_pet
from .object_memory_codec import decode_object_memory
from .settings_codec import decode_settings
from .social_history_codec import decode_social_history
from .world_codec import decode_world


def _older_fields(raw: Any, defaults: dict[str, Any], context: str) -> dict[str, Any]:
    row = object_fields(raw, (), optional=defaults, context=context)
    return {**defaults, **row}


def decode_legacy_session(
    contents: bytes, definitions: tuple[ObjectDefinition, ...], *, now: float,
) -> LoadedPetData:
    row = object_fields(
        decode_json(contents.decode("utf-8")), ("version", "pet"),
        optional=("settings", "adaptive", "world", "object_memory", "social_history"),
        context="legacy save",
    )
    if type(row["version"]) is not int or row["version"] != 1:
        raise ValueError("Unsupported legacy save version")
    pet = decode_legacy_pet(row["pet"], now=now)
    settings = decode_settings(_older_fields(
        row.get("settings", {}), PetSettings().to_dict(), "legacy settings",
    ))
    adaptive = decode_adaptive(_older_fields(
        row.get("adaptive", {}), encode_adaptive(AdaptiveMemory()), "legacy adaptive",
    ))
    world = decode_world(row["world"], definitions) if "world" in row else None
    memory = None
    if "object_memory" in row:
        if world is None:
            raise ValueError("Object memory requires its paired saved World")
        memory = decode_object_memory(row["object_memory"], {
            item.food_id or item.definition_id:
            "drink" if ObjectInteraction.DRINK in item.interactions else "food"
            for item in definitions
        }, allocated_until=world.next_instance_id)
    history = (decode_social_history(row["social_history"])
               if "social_history" in row else SocialContentHistory())
    return LoadedPetData(pet, settings, adaptive, True, world, memory, history)
