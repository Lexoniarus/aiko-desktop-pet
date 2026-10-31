"""Shared immutable Moodlet identities and semantic outcomes, without state."""

from enum import StrEnum


class MoodletId(StrEnum):
    CURSOR_CURIOSITY = "cursor_curiosity"
    CURSOR_FEAR = "cursor_fear"
    FOOD_FULFILLED = "food_fulfilled"
    SHARED_PLAY = "shared_play"
    PRIDE = "pride"
    RELIEF = "relief"
    CONNECTION = "connection"
    CHEERFUL = "cheerful"
    ENTHUSIASTIC = "enthusiastic"
    SECURE = "secure"
    POKING = "poking"
    CROWDED = "crowded"
    FOOD_MONOTONY = "food_monotony"
    WITHHELD = "withheld"
    DISRUPTED = "disrupted"
    HUNGER_WORN = "hunger_worn"
    EXHAUSTION_IRRITATED = "exhaustion_irritated"
    UNSTIMULATED = "unstimulated"
    LONELY = "lonely"
    MISSING_CLOSENESS = "missing_closeness"
    DISAPPOINTED = "disappointed"
    FOOD_WISH_DISREGARDED = "food_wish_disregarded"
    TRUSTING = "trusting"
    APPRECIATED = "appreciated"
    OPTIMISTIC = "optimistic"
    UNCERTAIN = "uncertain"
    OVERLOOKED = "overlooked"
    GUARDED = "guarded"


class MoodletOutcome(StrEnum):
    UNKNOWN = "unknown"
    COMPLETED = "completed"
    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    HANDOVER = "handover"
    INTAKE = "intake"
