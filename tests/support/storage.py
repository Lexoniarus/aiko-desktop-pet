"""Shared storage fixtures without importing test cases."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import (
    BUFFERED_CATEGORIES,
    SocialCategory,
    SocialProvider,
)
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.application.social_requests import (
    SocialProviderBlock,
    SocialRequestHistory,
    SocialRequestReceipt,
)
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.infrastructure.object_memory_codec import encode_object_memory
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.infrastructure.social_history_codec import encode_social_history
from aiko_pet.infrastructure.world_catalog import build_consumable_definitions
from aiko_pet.infrastructure.world_codec import encode_world
from aiko_pet.pet.care_evidence import CareActivity, CareExperience, LongTermProgress
from aiko_pet.pet.food_catalog import DEFAULT_CATALOG
from aiko_pet.pet.food_handover import FoodHandoverReceipt, FoodWishSnapshot
from aiko_pet.pet.mind.adaptive_models import SLOTS, AdaptiveMemory
from aiko_pet.pet.mind.object_knowledge import (
    ObjectMemorySnapshot,
    SavedObjectKnowledge,
)
from aiko_pet.pet.mind.quiet_rhythm import QuietPhase, QuietWindow
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlet_models import MoodletState, PoorCareCursor, PoorCareEvidence
from aiko_pet.pet.moodlets import MoodletGroup, MoodletOutcome
from aiko_pet.pet.need_exposure import ExposureMark
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import WishArea, WishId, WishState
from aiko_pet.world.contracts import ObjectDefinition, ObjectFootprint, WorldSurface
from aiko_pet.world.state import WorldState
from support.care import emotional_state
from support.horoscope import coordinator

WALL = 1800000000.0


def definitions() -> tuple[ObjectDefinition, ...]:
    return build_consumable_definitions(DEFAULT_CATALOG, load_item_catalog())


def legacy_payload() -> dict[str, Any]:
    pet = PetState(
        updated_at=WALL,
        lived_seconds=100000,
        moodlets=complete_emotional_state(),
        wishes=handover_state(),
    )
    stock = WorldState(WorldSurface(800, 600), definitions())
    item = stock.place_resting("apple", 100, ObjectFootprint(8, 8))
    world = stock.snapshot()
    memory = ObjectMemorySnapshot(
        (
            SavedObjectKnowledge(
                "memory_1",
                "apple",
                "food",
                100,
                0,
                True,
                80,
                True,
                None,
                instance_id=item.instance_id,
            ),
        ),
        2,
    )
    return {
        "version": 1,
        "pet": encode_pet_state(pet),
        "settings": PetSettings(scale=2, zodiac_sign="leo").to_dict(),
        "adaptive": profile().to_dict(),
        "social_history": encode_social_history(social_history()),
        "world": encode_world(world, recovery_x=0),
        "object_memory": encode_object_memory(
            memory, world_next_id=world.next_instance_id
        ),
    }


def timestamp(day: str = "2026-10-12", hour: int = 12) -> float:
    return datetime.fromisoformat(f"{day}T{hour:02d}:00:00").astimezone().timestamp()


def profile() -> AdaptiveMemory:
    return AdaptiveMemory(
        hour_seconds=[10.123456789 + i / 10000 for i in range(SLOTS)],
        busy_seconds=[4.123456789] * SLOTS,
        present_seconds=[9.123456789] * SLOTS,
        observed_days=[0.123456789] * SLOTS,
        last_slot_key="2026-10-24T15",
        profile_day="2026-10-24",
        strain=23.123456789,
        settled_work=0.123456789,
        session_seconds=7200.123456789,
        rest_seconds=100.123456789,
        last_session_seconds=3600.123456789,
        last_work_wall=1780000000.1234567,
        last_contact_wall=1780000001.1234567,
        last_seen_wall=1780000002.1234567,
        quiet_window=QuietWindow(
            1380.123456789,
            420.23456789,
            (
                QuietPhase("2026-10-21", 1380.123456789, 420.23456789),
                QuietPhase("2026-10-22", 1390.123456789, 430.23456789),
            ),
            "2026-10-22",
        ),
    )


def complete_emotional_state() -> MoodletState:
    source = emotional_state()
    assert source.care_evidence is not None
    evidence = replace(
        source.care_evidence,
        next_encounter_id=200,
        next_experience_id=900,
        progress=tuple(
            (
                LongTermProgress(definition.id, 86400, 86400, 90000, 123.5, 500.25)
                for definition in MOODLET_CATALOG.definitions.values()
                if definition.group == MoodletGroup.LONG_TERM
            )
        ),
        experiences=(
            *source.care_evidence.experiences,
            CareExperience(
                "withheld:1",
                88000,
                CareActivity.WITHHOLDING,
                MoodletOutcome.COMPLETED,
                upsetting=True,
                boundary_violated=True,
                object_id="object_99",
            ),
        ),
    )
    mark = ExposureMark(100, 30, 10)
    poor = PoorCareEvidence(0, (PoorCareCursor(mark, mark),) * 5)
    return replace(source, care_evidence=evidence, poor_care=poor)


def handover_state() -> WishState:
    desired, excluded = (
        WISH_CATALOG.definitions[key] for key in (WishId.FOOD, WishId.AVOID_FOOD)
    )
    context = (
        FoodWishSnapshot(
            10, desired.id, desired.bind_target("apple"), desired.goal, 100, 200, True
        ),
        FoodWishSnapshot(
            11, excluded.id, excluded.bind_target("donut"), excluded.goal, 110
        ),
    )
    return WishState(
        30,
        last_created_by_area=((WishArea.FOOD, 110),),
        last_expressed_at=200,
        refresh_at=1200,
        food_handovers=(
            FoodHandoverReceipt("offer:first", "object_99", 500.125, context),
            FoodHandoverReceipt("offer:second", "object_100", 600.375, context[:1]),
        ),
    )


def admitted_day():
    day = coordinator()[0].start("object_1")
    assert day is not None
    return day


def social_history() -> SocialContentHistory:
    entries = []
    for index in range(100):
        for offset, category in enumerate(BUFFERED_CATEGORIES):
            identity = (
                f"uselessfacts:fact-{index}"
                if category == SocialCategory.FACT
                else f"jokeapi:{100 + index}"
                if category == SocialCategory.TWO_PARTS
                else f"zitat-service:{index}"
                if index % 2 == 0
                else f"jokeapi:{index}"
            )
            entries.append(
                SocialContentReceipt(
                    category, identity, f"{3 * index + offset:064x}", index % 3
                )
            )
    requests = SocialRequestHistory(
        (
            SocialRequestReceipt(SocialProvider.FACTS, 1800000000.1234567),
            SocialRequestReceipt(SocialProvider.QUOTATIONS, 1800000002.1234567),
            SocialRequestReceipt(SocialProvider.JOKEAPI, 1799999999.1234567),
        ),
        (
            SocialProviderBlock(SocialProvider.QUOTATIONS, 1800003600.1234567),
            SocialProviderBlock(SocialProvider.FACTS, 1799999000.1234567),
        ),
    )
    return SocialContentHistory(tuple(entries), requests)
