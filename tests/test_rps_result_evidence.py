"""Actual RPS hands stay consistent and bounded by the existing Moodlet cause."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from itertools import product
from pathlib import Path
from typing import Any

from test_everyday_experiences import pet_at
from test_wish_assignment import wish
from test_wish_game_assignment import INPUTS, coordinator, pet_with

from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.application.settings import PetSettings
from aiko_pet.games.contracts import (
    GameId,
    GameResult,
    GameRoundEvent,
    RockPaperScissorsDetails,
    RockPaperScissorsMove,
)
from aiko_pet.games.rock_paper_scissors import Move, RockPaperScissors
from aiko_pet.infrastructure.moodlet_cause_codec import (
    decode_moodlet_causes,
    encode_moodlet_cause,
)
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.infrastructure.sqlite.moodlet_cause_rows import read_causes
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.fun import GameExperience
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
from aiko_pet.pet.wishes import WishId
from tools.persistence_test_support import save_test_session

WALL = 1800000000


def rps_cause() -> MoodletCause:
    return MoodletCause(
        MoodletCauseKind.INTERACTION, 50, "play:rock_paper_scissors:test:1",
        MoodletAttribution.USER, target_id=GameId.ROCK_PAPER_SCISSORS.value,
        outcome=MoodletOutcome.WIN,
        game_details=RockPaperScissorsDetails(Move.SCISSORS, Move.ROCK),
    )


def pet_with_cause(cause: MoodletCause) -> PetState:
    return PetState(
        updated_at=WALL, lived_seconds=100,
        moodlets=MoodletState(next_instance_id=2, active=(
            MoodletEpisode(
                1, MoodletId.SHARED_PLAY, 1, 50, 50, 7200,
                attribution=MoodletAttribution.USER, causes=(cause,),
            ),
        )),
    )


class RpsEvidenceContractTests(unittest.TestCase):
    def test_nine_pairs_use_canonical_moves_and_result_perspective(self) -> None:
        self.assertIs(Move, RockPaperScissorsMove)
        wins = {(Move.ROCK, Move.SCISSORS), (Move.PAPER, Move.ROCK),
                (Move.SCISSORS, Move.PAPER)}
        for player, aiko in product(Move, repeat=2):
            with self.subTest(player=player, aiko=aiko):
                details = RockPaperScissorsDetails(player, aiko)
                expected = "draw" if player == aiko else (
                    "win" if (player, aiko) in wins else "loss"
                )
                self.assertEqual(details.player_outcome, expected)
                self.assertEqual(details.aiko_outcome, (
                    "loss" if expected == "win" else
                    "win" if expected == "loss" else "draw"
                ))
                event = GameRoundEvent(
                    GameId.ROCK_PAPER_SCISSORS, "round", 1,
                    details.player_outcome, details,
                )
                self.assertEqual(event.details, details)

    def test_start_wrong_game_or_wrong_outcome_cannot_carry_hands(self) -> None:
        details = RockPaperScissorsDetails(Move.ROCK, Move.SCISSORS)
        cases: tuple[tuple[GameId, GameResult | None], ...] = (
            (GameId.ROCK_PAPER_SCISSORS, None),
            (GameId.ROCK_PAPER_SCISSORS, "loss"),
            (GameId.BLACKJACK, "win"),
        )
        for game, outcome in cases:
            with (
                self.subTest(game=game, outcome=outcome),
                self.assertRaises(ValueError),
            ):
                GameRoundEvent(game, "round", 1, outcome, details)
        invalid: Any = "rock"
        with self.assertRaises(ValueError):
            RockPaperScissorsDetails(invalid, Move.PAPER)

    def test_cause_rejects_wrong_game_and_wrong_aiko_result(self) -> None:
        for update in (
            {"target_id": "mastermind"}, {"outcome": MoodletOutcome.LOSS},
        ):
            with self.subTest(update=update), self.assertRaises(ValueError):
                replace(rps_cause(), **update)


class RpsEvidenceStorageTests(unittest.TestCase):
    def test_codec_keeps_hands_and_accepts_older_missing_details(self) -> None:
        for cause in (rps_cause(), replace(rps_cause(), game_details=None)):
            with self.subTest(details=cause.game_details):
                encoded = encode_moodlet_cause(cause)
                self.assertEqual(
                    "game_details" in encoded, cause.game_details is not None,
                )
                self.assertEqual(decode_moodlet_causes(
                    [encoded], started=50, trigger=50, key=MoodletId.SHARED_PLAY,
                    baseline=0,
                ), (cause,))

    def test_codec_rejects_unknown_extra_or_inconsistent_details(self) -> None:
        for update in (
            {"player_move": "lizard"}, {"aiko_move": True},
            {"game_id": "blackjack"}, {"player_move": "paper"}, {"score": 4},
        ):
            encoded = encode_moodlet_cause(rps_cause())
            encoded["game_details"].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                decode_moodlet_causes(
                    [encoded], started=50, trigger=50,
                    key=MoodletId.SHARED_PLAY, baseline=0,
                )

    def test_real_store_reopens_optional_details_without_changing_old_snapshots(self):
        with tempfile.TemporaryDirectory(prefix="aiko-rps-store-") as folder:
            for index, details in enumerate((rps_cause().game_details, None)):
                path = Path(folder) / f"{index}.sqlite3"
                pet = pet_with_cause(replace(rps_cause(), game_details=details))
                revision = save_test_session(SqliteStateStore(path), pet, PetSettings())
                restored = SqliteStateStore(path).load_session(now=WALL)
                self.assertEqual(
                    restored.state.capture_checkpoint(), pet.capture_checkpoint(),
                )
                self.assertEqual(restored.revision, revision)
                with closing(sqlite3.connect(path)) as connection:
                    raw = connection.execute(
                        "SELECT details_snapshot FROM moodlet_causes"
                    ).fetchone()[0]
                    snapshot = json.loads(raw)
                    self.assertEqual(snapshot["version"], 2 if details else 1)
                    self.assertEqual("game_details" in snapshot, details is not None)

    def test_invalid_sql_detail_envelopes_are_not_silently_downgraded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="aiko-rps-rows-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet_with_cause(rps_cause()),
                              PetSettings())
            with closing(sqlite3.connect(path)) as connection:
                for snapshot in (
                    dict(version=True, game=None, period=None),
                    dict(version=2, game=None, period=None, game_details=None),
                    dict(version=1, game=None, period=None, game_details={}),
                ):
                    connection.execute(
                        "UPDATE moodlet_causes SET details_snapshot = ?",
                        (json.dumps(snapshot),),
                    )
                    with self.subTest(snapshot=snapshot), self.assertRaises(ValueError):
                        read_causes(connection)


def finish_actual_round(
    runtime: GameExperienceCoordinator, number: int, player: Move, aiko: Move,
) -> GameRoundEvent:
    game = RockPaperScissors(random_index=lambda _size: tuple(Move).index(aiko))
    game.begin(player)
    start = GameRoundEvent(GameId.ROCK_PAPER_SCISSORS, "actual", number)
    runtime.observe_round(start, INPUTS)
    revealed = game.reveal()
    event = replace(start, outcome=revealed.outcome.value, details=revealed.details)
    runtime.observe_round(event, INPUTS)
    return event


class RpsEvidenceIntegrationTests(unittest.TestCase):
    def test_revealed_win_reaches_original_wish_cause_and_real_sqlite_restart(self):
        pet = pet_with(wish(WishId.WIN_ROUND, "rock_paper_scissors"))
        runtime = coordinator(pet)
        start = GameRoundEvent(GameId.ROCK_PAPER_SCISSORS, "actual", 1)
        runtime.observe_round(start, INPUTS)
        self.assertFalse(pet.moodlets.active)
        self.assertEqual(len(pet.wishes.active), 1)
        event = finish_actual_round(runtime, 1, Move.SCISSORS, Move.ROCK)
        self.assertFalse(pet.wishes.active)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(cause.game_details, event.details)
        self.assertEqual(cause.outcome, MoodletOutcome.WIN)
        assert cause.wish is not None
        self.assertEqual(cause.wish.objective, "next_win")
        checkpoint = pet.capture_checkpoint()
        runtime.observe_round(event, INPUTS)
        self.assertEqual(pet.capture_checkpoint(), checkpoint)
        with tempfile.TemporaryDirectory(prefix="aiko-rps-wish-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            self.assertEqual(
                SqliteStateStore(path).load_session(now=WALL).state.moodlets,
                pet.moodlets,
            )

    def test_cumulative_play_keeps_only_the_triggering_round_hands(self) -> None:
        pet = pet_with(wish(WishId.PLAY_GAME, "rock_paper_scissors"))
        finish_actual_round(coordinator(pet), 1, Move.PAPER, Move.ROCK)
        self.assertFalse(pet.moodlets.active)
        pet = decode_pet_state(encode_pet_state(pet), now=WALL)
        event = finish_actual_round(coordinator(pet), 2, Move.SCISSORS, Move.SCISSORS)
        cause = pet.moodlets.active[0].causes[0]
        self.assertEqual(cause.game_details, event.details)
        self.assertEqual(cause.outcome, MoodletOutcome.COMPLETED)
        assert cause.game is not None
        self.assertEqual(cause.game.round_outcome, MoodletOutcome.DRAW)
        self.assertEqual((cause.game.completed_rounds, cause.game.losses), (2, 1))

    def test_failed_nonloss_wish_retains_the_actual_losing_hands(self) -> None:
        pet = pet_with(wish(WishId.AVOID_ROUND_LOSS, "rock_paper_scissors"))
        event = finish_actual_round(coordinator(pet), 1, Move.PAPER, Move.ROCK)
        episode = pet.moodlets.active[0]
        self.assertEqual(episode.definition_id, MoodletId.DISAPPOINTED)
        self.assertEqual(episode.causes[0].game_details, event.details)
        self.assertEqual(episode.causes[0].outcome, MoodletOutcome.LOSS)
        self.assertEqual(
            decode_pet_state(encode_pet_state(pet), now=WALL).moodlets,
            pet.moodlets,
        )

    def test_existing_shared_play_without_wish_gets_the_final_actual_hands(self):
        pet = pet_at(10000)
        runtime = coordinator(pet)
        finish_actual_round(runtime, 1, Move.ROCK, Move.ROCK)
        event = finish_actual_round(runtime, 2, Move.ROCK, Move.SCISSORS)
        self.assertFalse(pet.moodlets.active)
        runtime.complete(GameExperience("rock_paper_scissors", 2, 0, 1, 1), INPUTS)
        self.assertEqual(len(pet.moodlets.active), 1)
        episode = pet.moodlets.active[0]
        self.assertEqual(episode.definition_id, MoodletId.SHARED_PLAY)
        self.assertEqual(episode.causes[0].game_details, event.details)
        self.assertIsNone(episode.causes[0].wish)
        pet.complete_play_session(
            game_id="rock_paper_scissors", session_id="actual",
            round_id=event.identity, game_details=event.details,
        )
        self.assertEqual(pet.moodlets.active[0], episode)

    def test_existing_comeback_without_wish_keeps_winning_hands(self) -> None:
        pet = pet_at(10000)
        runtime = coordinator(pet)
        finish_actual_round(runtime, 1, Move.PAPER, Move.ROCK)
        finish_actual_round(runtime, 2, Move.ROCK, Move.SCISSORS)
        event = finish_actual_round(runtime, 3, Move.SCISSORS, Move.ROCK)
        episode = pet.moodlets.active[0]
        self.assertEqual(episode.definition_id, MoodletId.PRIDE)
        self.assertEqual(episode.causes[0].game_details, event.details)
        self.assertIsNone(episode.causes[0].wish)

    def test_cause_cap_decay_and_removal_remove_sql_details_with_the_cause(self):
        causes = tuple(replace(rps_cause(), occurred_at=10 * n, event_id=f"round:{n}")
                       for n in range(1, 6))
        episode = MoodletEpisode(
            1, MoodletId.SHARED_PLAY, 3, 10, 50, 7200, causes=causes,
        )
        pet = PetState(updated_at=WALL, lived_seconds=100,
                       moodlets=MoodletState(next_instance_id=2, active=(episode,)))
        with tempfile.TemporaryDirectory(prefix="aiko-rps-cap-") as folder:
            path = Path(folder) / "state.sqlite3"
            store = SqliteStateStore(path)
            for active, expected in (
                ((episode,), 3), ((replace(episode, level=1),), 1), ((), 0),
            ):
                pet._change(moodlets=replace(pet.moodlets, active=active))
                save_test_session(store, pet, PetSettings())
                restored = SqliteStateStore(path).load_session(now=WALL).state
                self.assertEqual(restored.moodlets, pet.moodlets)
                with closing(sqlite3.connect(path)) as connection:
                    self.assertEqual(connection.execute(
                        "SELECT COUNT(*) FROM moodlet_causes"
                    ).fetchone()[0], expected)


if __name__ == "__main__":
    unittest.main()
