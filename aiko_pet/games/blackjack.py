"""Finite-deck Blackjack with explicit reveal and completed-hand accounting."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum
from random import shuffle

from .contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    GameId,
    RoundOutcome,
    SessionSummary,
)
from .playing_cards import STANDARD_DECK, Card


def hand_total(cards: tuple[Card, ...]) -> int:
    total = sum(11 if c.rank == "A" else (
        10 if c.rank in ("J", "Q", "K") else int(c.rank)
    ) for c in cards)
    aces = sum(c.rank == "A" for c in cards)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total


class Phase(str, Enum):
    PLAYER = "player"
    DEALER = "dealer"
    RESULT = "result"


@dataclass(frozen=True, slots=True)
class Table:
    player: tuple[Card, ...]
    dealer: tuple[Card | None, ...]
    player_total: int
    phase: Phase
    result: RoundOutcome | None  # Player's result, only after settlement.


class Blackjack:
    def __init__(
        self, *, shuffle_deck: Callable[[list[Card]], None] = shuffle,
    ) -> None:
        self._shuffle = shuffle_deck
        self._score = SessionSummary(GameId.BLACKJACK)
        self._closed = False
        self._begin()

    @property
    def score(self) -> SessionSummary:
        return self._score

    @property
    def result_details(self) -> BlackjackDetails | None:
        """Expose facts only after the existing reveal and score settlement."""
        return self._result_details if self._settled else None

    @property
    def table(self) -> Table:
        dealer: tuple[Card | None, ...] = (
            self._dealer if self._revealed else (self._dealer[0], None)
        )
        return Table(
            self._player, dealer, hand_total(self._player), self._phase,
            self._outcome if self._settled else None,
        )

    def _begin(self) -> None:
        self._deck = list(STANDARD_DECK)
        self._shuffle(self._deck)
        if len(self._deck) != 52 or set(self._deck) != set(STANDARD_DECK):
            raise ValueError("Shuffling must preserve the deck")
        first_player, first_dealer = self._draw(), self._draw()
        self._player: tuple[Card, ...] = (first_player, self._draw())
        self._dealer: tuple[Card, ...] = (first_dealer, self._draw())
        self._revealed = False
        self._settled = False
        self._outcome: RoundOutcome | None = None
        self._result_details: BlackjackDetails | None = None
        self._phase = Phase.PLAYER
        player_natural = hand_total(self._player) == 21
        dealer_natural = hand_total(self._dealer) == 21
        if player_natural or dealer_natural:
            reason = (
                BlackjackDecisionReason.BOTH_BLACKJACK
                if player_natural and dealer_natural else
                BlackjackDecisionReason.PLAYER_BLACKJACK if player_natural else
                BlackjackDecisionReason.AIKO_BLACKJACK
            )
            self._finish("draw" if player_natural and dealer_natural else (
                "win" if player_natural else "loss"
            ), reason)

    def _draw(self) -> Card:
        return self._deck.pop()

    def hit(self) -> None:
        self._require(Phase.PLAYER)
        self._player += (self._draw(),)
        value = hand_total(self._player)
        if value > 21:
            self._finish("loss", BlackjackDecisionReason.PLAYER_BUST)
        elif value == 21:
            self._phase = Phase.DEALER

    def stand(self) -> None:
        self._require(Phase.PLAYER)
        self._phase = Phase.DEALER

    def reveal_dealer(self) -> None:
        if self._closed or self._phase is Phase.PLAYER:
            raise ValueError("Cannot reveal before the player's turn ends")
        self._revealed = True

    def dealer_step(self) -> None:
        self._require(Phase.DEALER)
        if not self._revealed:
            raise ValueError("Reveal before dealing")
        if hand_total(self._dealer) < 17:
            self._dealer += (self._draw(),)
        value = hand_total(self._dealer)
        if value >= 17:
            player = hand_total(self._player)
            reason = (
                BlackjackDecisionReason.AIKO_BUST if value > 21 else
                BlackjackDecisionReason.EQUAL_TOTAL if player == value else
                BlackjackDecisionReason.HIGHER_TOTAL
            )
            self._finish("win" if value > 21 or player > value else (
                "loss" if player < value else "draw"
            ), reason)

    def _finish(self, outcome: RoundOutcome, reason: BlackjackDecisionReason) -> None:
        details = BlackjackDetails(
            hand_total(self._player), hand_total(self._dealer), reason,
        )
        if details.player_outcome != outcome:
            raise ValueError("Blackjack decision does not match its result")
        self._outcome = outcome
        self._result_details = details
        self._phase = Phase.RESULT

    def settle(self) -> None:
        self._require(Phase.RESULT)
        if not self._revealed or self._settled:
            raise ValueError("No newly revealed result")
        self._score = replace(
            self._score, wins=self._score.wins + (self._outcome == "win"),
            losses=self._score.losses + (self._outcome == "loss"),
            draws=self._score.draws + (self._outcome == "draw"),
        )
        self._settled = True

    def next_round(self) -> None:
        if self._closed or not self._settled:
            raise ValueError("Finish the current hand first")
        self._begin()

    def _require(self, phase: Phase) -> None:
        if self._closed or self._phase is not phase:
            raise ValueError("Action is not legal in this phase")

    def cancel(self) -> None:
        self._closed = True
