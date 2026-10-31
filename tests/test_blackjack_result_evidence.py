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

from test_blackjack import arranged_game, card
from test_everyday_experiences import pet_at
from test_rps_result_evidence import WALL, pet_with_cause, rps_cause
from test_wish_assignment import wish
from test_wish_game_assignment import INPUTS, coordinator, pet_with

from aiko_pet.application.game_experience import GameExperienceCoordinator
from aiko_pet.application.settings import PetSettings
from aiko_pet.games.blackjack import Blackjack, Phase
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
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.moodlets import (
    MoodletAttribution,
    MoodletCause,
    MoodletCauseKind,
    MoodletId,
    MoodletOutcome,
)
from aiko_pet.pet.wishes import WishId
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
    runtime: GameExperienceCoordinator, game: Blackjack, number: int = 1,
) -> GameRoundEvent:
    start = GameRoundEvent(GameId.BLACKJACK, "actual", number)
    runtime.observe_round(start, INPUTS)
    details = settle_game(game)
    event = replace(start, outcome=details.player_outcome, details=details)
    runtime.observe_round(event, INPUTS)
    return event


class BlackjackEvidenceSourceTests(unittest.TestCase):
    def test_actual_decks_supply_all_reasons_only_after_reveal_and_settlement(self):
        cases = (
            ((card("A"), card("8"), card("K"), card("9")), False,
             BlackjackDetails(21, 17, REASON.PLAYER_BLACKJACK)),
            ((card("9"), card("A"), card("8"), card("K")), False,
             BlackjackDetails(17, 21, REASON.AIKO_BLACKJACK)),
            ((card("A"), card("A", "hearts"), card("K"), card("K", "hearts")),
             False, BlackjackDetails(21, 21, REASON.BOTH_BLACKJACK)),
            ((card("10"), card("9"), card("8"), card("7"), card("K")), False,
             BlackjackDetails(18, 26, REASON.AIKO_BUST)),
            ((card("10"), card("2"), card("8"), card("3"), card("9")), True,
             BlackjackDetails(27, 5, REASON.PLAYER_BUST)),
            ((card("10"), card("9"), card("K"), card("8")), False,
             BlackjackDetails(20, 17, REASON.HIGHER_TOTAL)),
            ((card("9"), card("10"), card("8"), card("K")), False,
             BlackjackDetails(17, 20, REASON.HIGHER_TOTAL)),
            ((card("10"), card("9"), card("8"), card("9", "hearts")), False,
             BlackjackDetails(18, 18, REASON.EQUAL_TOTAL)),
            ((card("10"), card("9"), card("5"), card("2"), card("6"),
              card("10", "hearts")), True,
             BlackjackDetails(21, 21, REASON.EQUAL_TOTAL)),
        )
        for cards, hit, expected in cases:
            with self.subTest(expected=expected):
                game = arranged_game(*cards)
                self.assertIsNone(game.result_details)
                if game.table.phase is Phase.PLAYER:
                    game.hit() if hit else game.stand()
                self.assertIsNone(game.result_details)
                game.reveal_dealer()
                while game.table.phase is Phase.DEALER:
                    game.dealer_step()
                self.assertIsNone(game.result_details)
                game.settle()
                self.assertEqual(game.result_details, expected)
                game.next_round()
                self.assertIsNone(game.result_details)


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


class BlackjackEvidenceIntegrationTests(unittest.TestCase):
    def test_original_win_and_failed_nonloss_wishes_retain_actual_decision(self):
        cases = (
            (WishId.WIN_ROUND, (card("9"), card("A"), card("8"), card("K")),
             MoodletId.PRIDE, MoodletOutcome.WIN, REASON.AIKO_BLACKJACK),
            (WishId.AVOID_ROUND_LOSS,
             (card("A"), card("8"), card("K"), card("9")),
             MoodletId.DISAPPOINTED, MoodletOutcome.LOSS, REASON.PLAYER_BLACKJACK),
        )
        with tempfile.TemporaryDirectory(prefix="aiko-blackjack-wish-") as folder:
            for index, case in enumerate(cases):
                wish_id, cards, moodlet_id, outcome, reason = case
                with self.subTest(wish=wish_id):
                    pet = pet_with(wish(wish_id, "blackjack"))
                    runtime = coordinator(pet)
                    event = finish_blackjack(runtime, arranged_game(*cards))
                    self.assertFalse(pet.wishes.active)
                    episode = pet.moodlets.active[0]
                    self.assertEqual(episode.definition_id, moodlet_id)
                    cause = episode.causes[0]
                    self.assertEqual(cause.game_details, event.details)
                    self.assertEqual(cause.outcome, outcome)
                    assert isinstance(cause.game_details, BlackjackDetails)
                    self.assertEqual(cause.game_details.reason, reason)
                    assert cause.wish is not None
                    self.assertEqual(cause.wish.definition_id, wish_id)
                    checkpoint = pet.capture_checkpoint()
                    runtime.observe_round(event, INPUTS)
                    self.assertEqual(pet.capture_checkpoint(), checkpoint)
                    path = Path(folder) / f"{index}.sqlite3"
                    save_test_session(SqliteStateStore(path), pet, PetSettings())
                    self.assertEqual(
                        SqliteStateStore(path).load_session(now=WALL).state.moodlets,
                        pet.moodlets,
                    )

    def test_cumulative_goal_survives_restart_and_keeps_only_final_round_totals(self):
        pet = pet_with(wish(WishId.PLAY_GAME, "blackjack"))
        finish_blackjack(coordinator(pet), arranged_game(
            card("A"), card("8"), card("K"), card("9"),
        ))
        self.assertFalse(pet.moodlets.active)
        with tempfile.TemporaryDirectory(prefix="aiko-blackjack-progress-") as folder:
            path = Path(folder) / "state.sqlite3"
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            pet = SqliteStateStore(path).load_session(now=WALL).state
            event = finish_blackjack(coordinator(pet), arranged_game(
                card("10"), card("9"), card("8"), card("9", "hearts"),
            ), 2)
            self.assertFalse(pet.wishes.active)
            cause = pet.moodlets.active[0].causes[0]
            self.assertEqual(cause.game_details, event.details)
            self.assertEqual(cause.outcome, MoodletOutcome.COMPLETED)
            assert cause.game is not None
            self.assertEqual(cause.game.round_outcome, MoodletOutcome.DRAW)
            self.assertEqual((cause.game.completed_rounds, cause.game.losses), (2, 1))
            save_test_session(SqliteStateStore(path), pet, PetSettings())
            self.assertEqual(
                SqliteStateStore(path).load_session(now=WALL).state.moodlets,
                pet.moodlets,
            )

    def test_shared_play_and_comeback_without_wish_retain_triggering_round(self):
        for comeback in (False, True):
            with self.subTest(comeback=comeback):
                pet = pet_at(10000)
                runtime = coordinator(pet)
                finish_blackjack(runtime, arranged_game(
                    card("A"), card("8"), card("K"), card("9"),
                ))
                if comeback:
                    finish_blackjack(runtime, arranged_game(
                        card("10"), card("9"), card("K"), card("8"),
                    ), 2)
                    event = finish_blackjack(runtime, arranged_game(
                        card("9"), card("A"), card("8"), card("K"),
                    ), 3)
                else:
                    event = finish_blackjack(runtime, arranged_game(
                        card("10"), card("9"), card("8"), card("9", "hearts"),
                    ), 2)
                    self.assertFalse(pet.moodlets.active)
                    runtime.complete(GameExperience("blackjack", 2, 0, 1, 1), INPUTS)
                self.assertEqual(len(pet.moodlets.active), 1)
                episode = pet.moodlets.active[0]
                self.assertEqual(episode.definition_id, (
                    MoodletId.PRIDE if comeback else MoodletId.SHARED_PLAY
                ))
                self.assertEqual(episode.causes[0].game_details, event.details)
                self.assertIsNone(episode.causes[0].wish)


if __name__ == "__main__":
    unittest.main()
