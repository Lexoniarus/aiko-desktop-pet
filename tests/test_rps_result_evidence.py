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

from aiko_pet.application.settings import PetSettings
from aiko_pet.games.contracts import (
    GameId,
    GameResult,
    GameRoundEvent,
    RockPaperScissorsDetails,
    RockPaperScissorsMove,
)
from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.infrastructure.moodlet_cause_codec import (
    decode_moodlet_causes,
    encode_moodlet_cause,
)
from aiko_pet.infrastructure.sqlite.moodlet_cause_rows import read_causes
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
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


if __name__ == "__main__":
    unittest.main()
