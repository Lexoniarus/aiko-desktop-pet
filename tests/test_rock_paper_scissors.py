"""Headless game rules and per-window-session scoring."""

from __future__ import annotations

import unittest

from aiko_pet.games.rock_paper_scissors import (
    Move, Outcome, RockPaperScissors,
)


class RockPaperScissorsTests(unittest.TestCase):
    def test_every_move_pair_has_correct_outcome(self) -> None:
        choices = (Move.ROCK, Move.PAPER, Move.SCISSORS)
        expected = (
            (Outcome.DRAW, Outcome.LOSS, Outcome.WIN),
            (Outcome.WIN, Outcome.DRAW, Outcome.LOSS),
            (Outcome.LOSS, Outcome.WIN, Outcome.DRAW),
        )
        for player_index, move in enumerate(choices):
            for aiko_index, outcome in enumerate(expected[player_index]):
                with self.subTest(player=move, aiko=aiko_index):
                    game = RockPaperScissors(
                        random_index=lambda _size, n=aiko_index: n,
                    )
                    game.begin(move)
                    self.assertEqual(game.score.games, 0)
                    result = game.reveal()
                    self.assertEqual(result.player, move)
                    self.assertEqual(result.aiko, choices[aiko_index])
                    self.assertEqual(result.outcome, outcome)
                    self.assertEqual(game.score.games, 1)

    def test_scores_accumulate_only_for_completed_rounds(self) -> None:
        selections = iter((2, 1, 1, 0))
        game = RockPaperScissors(
            random_index=lambda _size: next(selections),
        )
        for move in (Move.ROCK, Move.ROCK, Move.ROCK, Move.ROCK):
            game.begin(move)
            game.reveal()
        self.assertEqual(game.score.games, 4)
        self.assertEqual(game.score.wins, 1)
        self.assertEqual(game.score.losses, 2)
        self.assertEqual(game.score.draws, 1)

    def test_pending_round_blocks_another_choice(self) -> None:
        game = RockPaperScissors(random_index=lambda _size: 0)
        game.begin(Move.PAPER)
        with self.assertRaises(RuntimeError):
            game.begin(Move.ROCK)
        self.assertEqual(game.reveal().aiko, Move.ROCK)

    def test_cancel_aborts_unrevealed_round_without_score(self) -> None:
        game = RockPaperScissors(random_index=lambda _size: 0)
        game.begin(Move.ROCK)
        game.cancel()
        self.assertFalse(game.pending)
        self.assertEqual(game.score.games, 0)
        game.begin(Move.PAPER)
        game.reveal()
        self.assertEqual(game.score.wins, 1)

    def test_invalid_opponent_and_player_moves_rejected(self) -> None:
        game = RockPaperScissors(random_index=lambda _size: 3)
        with self.assertRaises(ValueError):
            game.begin(Move.ROCK)
        self.assertFalse(game.pending)
        with self.assertRaises(ValueError):
            game.begin("rock")  # type: ignore[arg-type]

    def test_cannot_reveal_without_pending_round(self) -> None:
        with self.assertRaises(RuntimeError):
            RockPaperScissors().reveal()

    def test_new_session_starts_with_zero_counters(self) -> None:
        earlier = RockPaperScissors(random_index=lambda _size: 0)
        earlier.begin(Move.ROCK)
        earlier.reveal()
        later = RockPaperScissors()
        self.assertEqual(earlier.score.games, 1)
        self.assertEqual(later.score.games, 0)


if __name__ == "__main__":
    unittest.main()
