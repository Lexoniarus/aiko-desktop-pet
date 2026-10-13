"""German spoken lines for Aiko's Schere–Stein–Papier game.

All wording belongs to the character bubble, never the input-only window.
"""

from __future__ import annotations

from ..games.rock_paper_scissors import Move, Outcome, Round, Score

_HANDS = {
    Move.ROCK: "✊🏻 Stein",
    Move.PAPER: "✋🏻 Papier",
    Move.SCISSORS: "✌🏻 Schere",
}


def welcome_line() -> str:
    return "Oh, spielen wir Schere, Stein, Papier? Wähl deine Hand!"


def countdown_line(number: int) -> str:
    """Three separate turns rather than a single composite count."""
    return {1: "Eins!", 2: "Zwei!", 3: "Drei!"}[number]


def hands_line(result: Round) -> str:
    return (
        f"Du hast {_HANDS[result.player]}!\n"
        f"Ich habe {_HANDS[result.aiko]}!"
    )


def outcome_line(result: Round) -> str:
    return {
        Outcome.WIN: "Hmpf ... du hast gewonnen! Gut gespielt!",
        Outcome.LOSS: "Hehe, diesmal habe ich gewonnen!",
        Outcome.DRAW: "Oh! Unentschieden! Wir denken wohl gleich.",
    }[result.outcome]


def score_line(score: Score) -> str:
    """Every counter is spoken, with no scoreboard in the input window."""
    rounds = "Runde" if score.games == 1 else "Runden"
    return (
        f"Unser Stand nach {score.games} {rounds}: "
        f"Du hast {score.wins} Siege, ich {score.losses}. "
        f"Unentschieden: {score.draws}. Noch eine Runde?"
    )
