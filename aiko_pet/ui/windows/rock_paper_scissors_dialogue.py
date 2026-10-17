"""Standalone game copy uses the same authored catalogue as the desktop mind."""

from __future__ import annotations

import time

from ...games.rock_paper_scissors import Outcome, Round
from ...pet.content import GERMAN_TEXT
from ...pet.mind.catalog import DialogueBook
from ...pet.mind.dialogue_context import DialogueContext, FriendshipStage
from ...pet.routine import context_at


class GameDialogue:
    """Own standalone game rotation; desktop games inject their session mind."""

    def __init__(self) -> None:
        self._book = DialogueBook.from_file()

    def choose(self, event: str, dialogue: DialogueContext | None = None) -> str:
        snapshot = dialogue or DialogueContext(
            FriendshipStage.ACQUAINTANCE, "calm", context_at(time.time()),
        )
        reaction = self._book.choose(
            event, snapshot.mood, snapshot.time, time.monotonic(),
            dialogue=snapshot, presentation="short",
        )
        if reaction is None:
            raise ValueError(f"Missing game dialogue: {event}")
        return reaction.text


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
