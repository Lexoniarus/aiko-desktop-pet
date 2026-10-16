"""Standalone game copy uses the same authored catalogue as the desktop mind."""

from __future__ import annotations

import time

from ...games.rock_paper_scissors import Outcome, Round
from ...pet.content import GERMAN_TEXT
from ...pet.mind.catalog import DialogueBook
from ...pet.mind.dialogue_context import DialogueContext, FriendshipStage
from ...pet.routine import context_at

_BOOK = DialogueBook.from_file()


def game_line(event: str, dialogue: DialogueContext | None = None) -> str:
    snapshot = dialogue or DialogueContext(
        FriendshipStage.ACQUAINTANCE,
        "calm",
        context_at(time.time()),
    )
    reaction = _BOOK.choose(
        event,
        snapshot.mood,
        snapshot.time,
        time.monotonic(),
        dialogue=snapshot,
        presentation="short",
    )
    if reaction is None:
        raise ValueError(f"Missing game dialogue: {event}")
    return reaction.text


def welcome_line(rounds: int = 0) -> str:
    return game_line("game_greeting")


def countdown_line(number: int) -> str:
    if number not in (1, 2, 3):
        raise KeyError(number)
    return GERMAN_TEXT.format(f"rps.countdown.{number}")


def outcome_event(result: Round) -> str:
    return {
        Outcome.WIN: "game_player_win",
        Outcome.LOSS: "game_aiko_win",
        Outcome.DRAW: "game_draw",
    }[result.outcome]


def outcome_line(result: Round, games: int = 1) -> str:
    return game_line(outcome_event(result))
