"""Shared games fixtures without importing test cases."""

from __future__ import annotations

from dataclasses import replace

from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.games.blackjack import Blackjack, Phase
from aiko_pet.games.contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    GameId,
    GameRoundEvent,
    RockPaperScissorsDetails,
    RoundOutcome,
)
from aiko_pet.games.playing_cards import STANDARD_DECK, Card
from aiko_pet.games.rock_paper_scissors import Move, RockPaperScissors
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletEpisode,
    MoodletId,
    MoodletOutcome,
    MoodletState,
)
from aiko_pet.pet.state import PetState
from support.wishes import INPUTS


def arranged_game(*cards: Card) -> Blackjack:
    def arrange(deck):
        deck[:] = [c for c in STANDARD_DECK if c not in cards] + list(reversed(cards))

    return Blackjack(shuffle_deck=arrange)


def card(rank: str, suit: str = "clubs") -> Card:
    return Card(suit, rank.zfill(2) if rank.isdecimal() else rank)


REASON = BlackjackDecisionReason
RESULTS: tuple[tuple[int, int, BlackjackDecisionReason, RoundOutcome], ...] = (
    (20, 26, REASON.AIKO_BUST, "win"),
    (30, 5, REASON.PLAYER_BUST, "loss"),
    (20, 21, REASON.AIKO_BLACKJACK, "loss"),
    (21, 16, REASON.PLAYER_BLACKJACK, "win"),
    (21, 21, REASON.BOTH_BLACKJACK, "draw"),
    (20, 18, REASON.HIGHER_TOTAL, "win"),
    (18, 20, REASON.HIGHER_TOTAL, "loss"),
    (18, 18, REASON.EQUAL_TOTAL, "draw"),
    (21, 21, REASON.EQUAL_TOTAL, "draw"),
)


def blackjack_cause(details: BlackjackDetails) -> MoodletCause:
    return MoodletCause(
        MoodletCauseKind.INTERACTION,
        50,
        "play:blackjack:test:1",
        MoodletAttribution.USER,
        target_id=GameId.BLACKJACK.value,
        outcome=MoodletOutcome(details.aiko_outcome),
        game_details=details,
    )


def settle_game(game: Blackjack, *, hit: bool = False) -> BlackjackDetails:
    """Advance only rule decisions; no scheduler, GUI or wall-clock waits."""
    if game.table.phase is Phase.PLAYER:
        game.hit() if hit else game.stand()
    game.reveal_dealer()
    while game.table.phase is Phase.DEALER:
        game.dealer_step()
    game.settle()
    details = game.result_details
    assert details is not None
    return details


def finish_blackjack(
    runtime: GameExperienceCoordinator, game: Blackjack, number: int = 1
) -> GameRoundEvent:
    start = GameRoundEvent(GameId.BLACKJACK, "actual", number)
    runtime.observe_round(start, INPUTS)
    details = settle_game(game)
    event = replace(start, outcome=details.player_outcome, details=details)
    runtime.observe_round(event, INPUTS)
    return event


WALL = 1800000000


def rps_cause() -> MoodletCause:
    return MoodletCause(
        MoodletCauseKind.INTERACTION,
        50,
        "play:rock_paper_scissors:test:1",
        MoodletAttribution.USER,
        target_id=GameId.ROCK_PAPER_SCISSORS.value,
        outcome=MoodletOutcome.WIN,
        game_details=RockPaperScissorsDetails(Move.SCISSORS, Move.ROCK),
    )


def pet_with_cause(cause: MoodletCause) -> PetState:
    return PetState(
        updated_at=WALL,
        lived_seconds=100,
        moodlets=MoodletState(
            next_instance_id=2,
            active=(
                MoodletEpisode(
                    1,
                    MoodletId.SHARED_PLAY,
                    1,
                    50,
                    50,
                    7200,
                    attribution=MoodletAttribution.USER,
                    causes=(cause,),
                ),
            ),
        ),
    )


def finish_actual_round(
    runtime: GameExperienceCoordinator, number: int, player: Move, aiko: Move
) -> GameRoundEvent:
    game = RockPaperScissors(random_index=lambda _size: tuple(Move).index(aiko))
    game.begin(player)
    start = GameRoundEvent(GameId.ROCK_PAPER_SCISSORS, "actual", number)
    runtime.observe_round(start, INPUTS)
    revealed = game.reveal()
    event = replace(start, outcome=revealed.outcome.value, details=revealed.details)
    runtime.observe_round(event, INPUTS)
    return event
