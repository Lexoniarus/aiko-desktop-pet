"""Shared care fixtures without importing test cases."""

from __future__ import annotations

from aiko_pet.pet.care_evidence import (
    CareActivity,
    CareEncounter,
    CareEvidenceState,
    CareExperience,
    CarePeriodSummary,
    LongTermProgress,
)
from aiko_pet.pet.care_experiences import record_experience
from aiko_pet.pet.friendship_history import FriendshipHistory
from aiko_pet.pet.long_term_moodlets import advance_long_term, prepare_long_term
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import (
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletGroup,
    MoodletId,
    MoodletOutcome,
    MoodletState,
    MoodletWishCause,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import (
    ActiveWish,
    GameWishProgress,
    WishArea,
    WishId,
    WishState,
    WishTargetKind,
)

EVERYDAY_EXPERIENCES_WALL = 1800000000


def pet_at(elapsed):
    return PetState(
        updated_at=EVERYDAY_EXPERIENCES_WALL,
        lived_seconds=elapsed,
        affection=20,
        friendship=60,
        moodlets=MoodletState(care_evidence=CareEvidenceState(0)),
    )


def everyday_experiences_families(pet):
    return {e.definition_id for e in pet.moodlets.active}


HOUR = 3600
DAY = 24 * HOUR
HISTORY = FriendshipHistory(baseline=0)


def contact(receipt, at, activity=CareActivity.SOCIAL, *, wish=None, win=False):
    area, kind, target = {
        CareActivity.SOCIAL: (WishArea.SOCIAL, WishTargetKind.SOCIAL, "chat"),
        CareActivity.PETTING: (WishArea.AFFECTION, WishTargetKind.CARE, "pet"),
        CareActivity.PLAY: (WishArea.GAMES, WishTargetKind.GAME, "mastermind"),
    }[activity]
    return CareExperience(
        receipt,
        at,
        activity,
        MoodletOutcome.WIN if win else MoodletOutcome.COMPLETED,
        area,
        kind,
        target,
        wish_instance_id=wish,
        pleasant=True,
    )


def upsetting(receipt, at, *, violation=True):
    return CareExperience(
        receipt,
        at,
        CareActivity.POKING,
        MoodletOutcome.COMPLETED,
        upsetting=True,
        boundary_violated=violation,
    )


def evaluate(events, *, history=HISTORY):
    state = prepare_long_term(MoodletState(), elapsed=0)
    for event in events:
        state = advance_long_term(
            state, history, elapsed=event.occurred_at, sleeping=False
        )
        state, _ = record_experience(state, event)
    return advance_long_term(state, history, elapsed=DAY, sleeping=False)


def long_term_moodlets_families(state):
    return {
        e.definition_id
        for e in state.active
        if MOODLET_CATALOG.definitions[e.definition_id].group == MoodletGroup.LONG_TERM
    }


CARE_EVIDENCE_STORAGE_ELAPSED = 90000
CARE_EVIDENCE_STORAGE_WALL = 1800000000


def emotional_state():
    evidence = CareEvidenceState(
        0,
        4,
        (
            CareEncounter(1, 100, 120),
            CareEncounter(2, 7500, 7520),
            CareEncounter(3, 30000, 30030),
        ),
        (
            CareExperience(
                "round:a:1",
                120,
                CareActivity.PLAY,
                MoodletOutcome.WIN,
                WishArea.GAMES,
                WishTargetKind.GAME,
                "mastermind",
                1,
                1,
                pleasant=True,
            ),
            CareExperience(
                "social:1",
                7520,
                CareActivity.SOCIAL,
                MoodletOutcome.COMPLETED,
                WishArea.SOCIAL,
                WishTargetKind.SOCIAL,
                "fact",
                2,
                2,
                pleasant=True,
            ),
            CareExperience(
                "social:2",
                30030,
                CareActivity.SOCIAL,
                MoodletOutcome.COMPLETED,
                WishArea.SOCIAL,
                WishTargetKind.SOCIAL,
                "chat",
                3,
                3,
                pleasant=True,
            ),
        ),
        (
            LongTermProgress(MoodletId.TRUSTING, 86400, 86400, 90000),
            LongTermProgress(MoodletId.APPRECIATED, 0, 0, 90000),
        ),
    )
    summary = CarePeriodSummary(
        0,
        86400,
        3,
        (CareActivity.PLAY, CareActivity.SOCIAL),
        3,
        (WishArea.GAMES, WishArea.SOCIAL),
        1,
    )
    trust = MoodletEpisode(
        1,
        MoodletId.TRUSTING,
        1,
        86400,
        86400,
        129600,
        causes=(
            MoodletCause(
                MoodletCauseKind.LONG_TERM,
                86400,
                "trust:0:86400",
                outcome=MoodletOutcome.COMPLETED,
                period=summary,
            ),
        ),
    )
    definition = WISH_CATALOG.definitions[WishId.PLAY_ANY_GAME]
    play = MoodletEpisode(
        2,
        MoodletId.SHARED_PLAY,
        3,
        80000,
        89000,
        3600,
        causes=(
            MoodletCause(
                MoodletCauseKind.WISH_FULFILLED,
                89000,
                "round:b:2",
                wish=MoodletWishCause(
                    7,
                    definition.id.value,
                    "",
                    "total_rounds",
                    2,
                    definition.bind_target(),
                ),
                target_id="connect_four",
                outcome=MoodletOutcome.COMPLETED,
            ),
        ),
        lower_stage_seconds=(4200, 2700),
    )
    food = WISH_CATALOG.definitions[WishId.AVOID_FOOD]
    refused = MoodletEpisode(
        3,
        MoodletId.FOOD_WISH_DISREGARDED,
        1,
        88000,
        88000,
        1800,
        causes=(
            MoodletCause(
                MoodletCauseKind.WISH_FAILED,
                88000,
                "offer:3",
                wish=MoodletWishCause(
                    8,
                    food.id.value,
                    "donut",
                    "food_handover",
                    0,
                    food.bind_target("donut"),
                ),
                target_id="donut",
                outcome=MoodletOutcome.HANDOVER,
                object_id="item:3",
                handed_over_at=87000,
            ),
        ),
    )
    return MoodletState(0, 4, (trust, play, refused), care_evidence=evidence)


EMOTIONAL_PERSISTENCE_WALL = 1800000000.0
EMOTIONAL_PERSISTENCE_ELAPSED = 1000.0


def moodlet_state() -> MoodletState:
    return MoodletState(
        100,
        8,
        (
            MoodletEpisode(1, MoodletId.POKING, 2, 100, 950, 570, (2, 3), 1),
            MoodletEpisode(
                3, MoodletId.HUNGER_WORN, 1, 200, 200, 2400, (1,), decay_paused=True
            ),
            MoodletEpisode(5, MoodletId.WITHHELD, 3, 300, 900, 1200, decay_paused=True),
            MoodletEpisode(7, MoodletId.PRIDE, 2, 800, 850, 3600),
        ),
    )


def wish_state() -> WishState:
    return WishState(
        6,
        (
            ActiveWish(1, WishId.FOOD, "apple", 100, 14500),
            ActiveWish(
                3,
                WishId.WIN_OVERALL,
                "blackjack",
                200,
                14600,
                900,
                GameWishProgress(("session-a:1", "session-b:1"), 1, 1),
            ),
            ActiveWish(5, WishId.PET, "pet", 300, 14700),
        ),
        ((WishArea.FOOD, 100), (WishArea.GAMES, 200), (WishArea.AFFECTION, 300)),
        900,
    )
