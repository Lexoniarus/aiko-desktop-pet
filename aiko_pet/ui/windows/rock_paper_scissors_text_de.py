"""Deterministic German game dialogue selected from packaged JSON copy."""

from __future__ import annotations

from ...games.rock_paper_scissors import Outcome, Round
from ...pet.content import GERMAN_TEXT


_WELCOME = tuple(GERMAN_TEXT.format(f"rps.welcome.{i}") for i in range(3))
_WIN = tuple(GERMAN_TEXT.format(f"rps.win.{i}") for i in range(3))
_LOSS = tuple(GERMAN_TEXT.format(f"rps.loss.{i}") for i in range(3))
_DRAW = tuple(GERMAN_TEXT.format(f"rps.draw.{i}") for i in range(3))


def welcome_line(rounds: int = 0) -> str:
    return _WELCOME[rounds % len(_WELCOME)]


def countdown_line(number: int) -> str:
    if number not in (1, 2, 3):
        raise KeyError(number)
    return GERMAN_TEXT.format(f"rps.countdown.{number}")


def outcome_line(result: Round, games: int = 1) -> str:
    lines = {
        Outcome.WIN: _WIN,
        Outcome.LOSS: _LOSS,
        Outcome.DRAW: _DRAW,
    }[result.outcome]
    return lines[(games - 1) % len(lines)]
