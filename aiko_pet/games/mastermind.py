"""Local code-setting rules. Hidden information never appears in round views."""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, replace
from secrets import choice
from typing import Literal

from .contracts import GameId, SessionSummary

COLORS = ("red", "yellow", "blue", "green", "purple", "white")
PLACES, ATTEMPTS = 4, 10
Code = tuple[str, ...]


def valid_code(code: Code) -> bool:
    return len(code) == PLACES and all(color in COLORS for color in code)


def new_code() -> Code:
    return tuple(choice(COLORS) for _ in range(PLACES))


@dataclass(frozen=True, slots=True)
class Feedback:
    exact: int
    misplaced: int


def evaluate(secret: Code, guess: Code) -> Feedback:
    if not valid_code(secret) or not valid_code(guess):
        raise ValueError("Expected four valid colors")
    exact = sum(a == b for a, b in zip(secret, guess))
    shared = sum((Counter(secret) & Counter(guess)).values())
    return Feedback(exact, shared - exact)


@dataclass(frozen=True, slots=True)
class Guess:
    colors: Code
    feedback: Feedback


@dataclass(frozen=True, slots=True)
class RoundView:
    guesses: tuple[Guess, ...] = ()
    result: Literal["win", "loss"] | None = None


class MastermindSession:
    """Sole mutable rules/score owner; no time limit and no pet-state writes."""

    def __init__(self, secret_factory: Callable[[], Code] = new_code) -> None:
        self._factory = secret_factory
        self._secret = self._make_secret()
        self._round = RoundView()
        self._score = SessionSummary(GameId.MASTERMIND)
        self._closed = self._settled = False

    def _make_secret(self) -> Code:
        code = tuple(self._factory())
        if not valid_code(code):
            raise ValueError("Invalid secret")
        return code

    @property
    def view(self) -> RoundView:
        return self._round

    @property
    def score(self) -> SessionSummary:
        return self._score

    def code_view(self, revealed: int = 0) -> tuple[str | None, ...]:
        if not 0 <= revealed <= PLACES or (revealed and self._round.result is None):
            raise ValueError("Cannot reveal a live code")
        return tuple(
            color if i < revealed else None for i, color in enumerate(self._secret)
        )

    def submit(self, colors: Code) -> Guess:
        if self._closed or self._round.result is not None:
            raise ValueError("Round is not accepting guesses")
        colors = tuple(colors)
        feedback = evaluate(self._secret, colors)
        guess = Guess(colors, feedback)
        guesses = (*self._round.guesses, guess)
        result: Literal["win", "loss"] | None = (
            "win"
            if feedback.exact == PLACES
            else "loss"
            if len(guesses) == ATTEMPTS
            else None
        )
        self._round = RoundView(guesses, result)
        return guess

    def settle(self) -> None:
        if self._closed or self._settled or self._round.result is None:
            raise ValueError("No new result to settle")
        self._score = replace(
            self._score,
            wins=self._score.wins + (self._round.result == "win"),
            losses=self._score.losses + (self._round.result == "loss"),
        )
        self._settled = True

    def next_round(self) -> None:
        if self._closed or not self._settled:
            raise ValueError("Finish the current round first")
        secret = self._make_secret()
        self._secret, self._round, self._settled = secret, RoundView(), False

    def cancel(self) -> None:
        self._closed = True
