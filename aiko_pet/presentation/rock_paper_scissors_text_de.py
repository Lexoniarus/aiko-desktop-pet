"""Deterministic German dialogue for Aiko's own game reactions only."""

from __future__ import annotations

from ..games.rock_paper_scissors import Outcome, Round

_WELCOME = (
    "Na, eine Runde Schere, Stein, Papier? Zeig mal deine Hand!",
    "Jetzt wird's ernst! Na gut ... was nimmst du?",
    "Hehe, bereit für eine Revanche? Such dir eine Hand aus!",
)
_WIN = (
    "Hmpf ... okay, der Punkt geht an dich. Diesmal!",
    "Oh, erwischt! Du hast mich echt ausgetrickst.",
    "Na toll ... das war eindeutig deine Runde.",
)
_LOSS = (
    "Ha! Den Punkt schnapp ich mir!",
    "Hehe, das lief doch ganz gut für mich!",
    "Yes! ... Ähm, ich meine: gut gespielt!",
)
_DRAW = (
    "Ha, dieselbe Hand! Wir sind wohl auf einer Wellenlänge.",
    "Och, ein Gleichstand? Na, das lösen wir noch!",
    "Unentschieden! Wir sollten's noch einmal versuchen.",
)


def welcome_line(rounds: int = 0) -> str:
    return _WELCOME[rounds % len(_WELCOME)]


def countdown_line(number: int) -> str:
    return {1: "Eins!", 2: "Zwei!", 3: "Drei!"}[number]


def outcome_line(result: Round, games: int = 1) -> str:
    lines = {
        Outcome.WIN: _WIN,
        Outcome.LOSS: _LOSS,
        Outcome.DRAW: _DRAW,
    }[result.outcome]
    return lines[(games - 1) % len(lines)]
