"""Blackjack result facts use the same bounded cause/store path as RPS."""

from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from test_rps_result_evidence import WALL, pet_with_cause, rps_cause

from aiko_pet.application.settings import PetSettings
from aiko_pet.games.contracts import (
    BlackjackDecisionReason,
    BlackjackDetails,
    GameId,
    GameRoundEvent,
    RoundOutcome,
)
from aiko_pet.infrastructure.moodlet_cause_codec import (
    decode_moodlet_causes,
    encode_moodlet_cause,
)
from aiko_pet.infrastructure.sqlite.store import SqliteStateStore
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletId,
    MoodletOutcome,
)
from tools.persistence_test_support import save_test_session

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
        MoodletCauseKind.INTERACTION, 50, "play:blackjack:test:1",
        MoodletAttribution.USER, target_id=GameId.BLACKJACK.value,
        outcome=MoodletOutcome(details.aiko_outcome), game_details=details,
    )


class BlackjackEvidenceContractTests(unittest.TestCase):
    def test_all_decisions_preserve_totals_and_player_aiko_orientation(self) -> None:
        self.assertEqual({case[2] for case in RESULTS}, set(BlackjackDecisionReason))
        for player, aiko, reason, expected in RESULTS:
            with self.subTest(reason=reason, player=player):
                details = BlackjackDetails(player, aiko, reason)
                self.assertEqual(details.player_outcome, expected)
                self.assertEqual(details.aiko_outcome, (
                    "loss" if expected == "win" else
                    "win" if expected == "loss" else "draw"
                ))
                self.assertEqual(GameRoundEvent(
                    GameId.BLACKJACK, "real", 1, expected, details,
                ).details, details)

    def test_invalid_totals_or_contradictory_reasons_are_rejected(self) -> None:
        invalid: tuple[tuple[Any, Any, Any], ...] = (
            (True, 18, REASON.HIGHER_TOTAL), (20.0, 18, REASON.HIGHER_TOTAL),
            (3, 18, REASON.HIGHER_TOTAL), (31, 18, REASON.PLAYER_BUST),
            (20, 27, REASON.AIKO_BUST), (20, 18, "higher_total"),
            (20, 18, REASON.PLAYER_BUST), (20, 18, REASON.AIKO_BUST),
            (20, 18, REASON.PLAYER_BLACKJACK), (21, 21, REASON.AIKO_BLACKJACK),
            (20, 21, REASON.BOTH_BLACKJACK), (18, 18, REASON.HIGHER_TOTAL),
            (20, 18, REASON.EQUAL_TOTAL), (18, 6, REASON.HIGHER_TOTAL),
        )
        for args in invalid:
            with self.subTest(args=args), self.assertRaises(ValueError):
                BlackjackDetails(*cast(Any, args))

    def test_start_wrong_game_or_wrong_result_cannot_carry_details(self) -> None:
        details = BlackjackDetails(20, 22, REASON.AIKO_BUST)
        with self.assertRaises(ValueError):
            GameRoundEvent(GameId.BLACKJACK, "real", 1, details=details)
        with self.assertRaises(ValueError):
            GameRoundEvent(GameId.ROCK_PAPER_SCISSORS, "real", 1, "win", details)
        with self.assertRaises(ValueError):
            GameRoundEvent(GameId.BLACKJACK, "real", 1, "loss", details)
        with self.assertRaises(ValueError):
            replace(blackjack_cause(details), target_id="rock_paper_scissors")


class BlackjackEvidenceStorageTests(unittest.TestCase):
    def test_codec_preserves_all_reasons_and_rejects_inconsistent_facts(self) -> None:
        for player, aiko, reason, _expected in RESULTS:
            cause = blackjack_cause(BlackjackDetails(player, aiko, reason))
            self.assertEqual(decode_moodlet_causes(
                [encode_moodlet_cause(cause)], started=50, trigger=50,
                key=MoodletId.SHARED_PLAY, baseline=0,
            ), (cause,))
        for update in (
            {"player_total": True}, {"reason": "lucky"}, {"score": 9},
            {"aiko_total": 18}, {"game_id": "mastermind"},
        ):
            encoded = encode_moodlet_cause(blackjack_cause(
                BlackjackDetails(20, 22, REASON.AIKO_BUST),
            ))
            encoded["game_details"].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                decode_moodlet_causes(
                    [encoded], started=50, trigger=50,
                    key=MoodletId.SHARED_PLAY, baseline=0,
                )

    def test_sqlite_reopens_blackjack_legacy_and_rps_in_existing_envelopes(self):
        actual = blackjack_cause(BlackjackDetails(20, 22, REASON.AIKO_BUST))
        cases = (actual, replace(actual, game_details=None), rps_cause())
        with tempfile.TemporaryDirectory(prefix="aiko-blackjack-store-") as folder:
            path = Path(folder) / "state.sqlite3"
            for cause in cases:
                pet = pet_with_cause(cause)
                revision = save_test_session(SqliteStateStore(path), pet, PetSettings())
                loaded = SqliteStateStore(path).load_session(now=WALL)
                self.assertEqual(
                    loaded.state.capture_checkpoint(), pet.capture_checkpoint(),
                )
                self.assertEqual(loaded.revision, revision)
                with closing(sqlite3.connect(path)) as connection:
                    row = json.loads(connection.execute(
                        "SELECT details_snapshot FROM moodlet_causes"
                    ).fetchone()[0])
                    self.assertEqual(
                        row["version"], 1 if cause.game_details is None else 2,
                    )


if __name__ == "__main__":
    unittest.main()
