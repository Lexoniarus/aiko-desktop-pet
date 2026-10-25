"""Dialogue fixtures independent of the packaged catalogue's source layout."""

from pathlib import Path
from typing import Any

from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.catalog import CATALOGUE
from aiko_pet.pet.mind.dialogue_context import (
    DialogueContext,
    FriendshipStage,
    ReactionTone,
    SituationalCondition,
)
from aiko_pet.pet.needs import NeedCondition
from aiko_pet.pet.routine import TimeContext


def _resource_object(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError(f"Expected resource object: {path}")
    return value


def dialogue_source_fixture() -> dict[str, Any]:
    """A fresh complete source for parser mutation tests, not the source index."""
    return _resource_object(CATALOGUE.parent / "events" / "contact.json")


def balance_source_fixture() -> dict[str, Any]:
    """Balance is a sibling resource of dialogues/, not of the German index."""
    return _resource_object(
        Path(__file__).resolve().parents[1] / "aiko_pet" / "data" / "balance.json"
    )


def dialogue_context(
    time: TimeContext,
    *,
    stage: FriendshipStage = FriendshipStage.ACQUAINTANCE,
    emotional_state: EmotionalState = EmotionalState.CALM,
    mood_value: float = 60,
    need_conditions: frozenset[NeedCondition] = frozenset(),
    reaction_tone: ReactionTone | None = None,
    situational_conditions: frozenset[SituationalCondition] = frozenset(),
    sleeping: bool = False,
    present: bool | None = None,
) -> DialogueContext:
    return DialogueContext(
        stage,
        mood_value,
        EmotionalComposition(emotional_state),
        time,
        need_conditions,
        reaction_tone,
        situational_conditions,
        sleeping,
        present=present,
    )
