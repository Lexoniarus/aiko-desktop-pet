"""Mastermind multiplicity, final-attempt outcome and secret ownership."""

import unittest
from itertools import product
from unittest.mock import Mock

from aiko_pet.games.mastermind import Feedback, MastermindSession, evaluate

SECRET = ("red", "red", "blue", "green")
MISS = ("white",) * 4


class MastermindRulesTests(unittest.TestCase):
    def test_example_and_duplicate_color_exhaustion(self):
        self.assertEqual(
            evaluate(SECRET, ("red", "blue", "red", "yellow")), Feedback(1, 2)
        )
        self.assertEqual(evaluate(SECRET, ("red",) * 4), Feedback(2, 0))
        self.assertEqual(evaluate(SECRET, SECRET), Feedback(4, 0))

    def test_all_three_color_codes_against_independent_consumption_oracle(self):
        codes = tuple(product(("red", "blue", "green"), repeat=4))
        for secret in codes:
            for guess in codes:
                unmatched_secret = [a for a, b in zip(secret, guess) if a != b]
                unmatched_guess = [b for a, b in zip(secret, guess) if a != b]
                exact = 4 - len(unmatched_secret)
                misplaced = 0
                for color in unmatched_guess:
                    if color in unmatched_secret:
                        unmatched_secret.remove(color)
                        misplaced += 1
                self.assertEqual(evaluate(secret, guess), Feedback(exact, misplaced))

    def test_invalid_and_incomplete_guesses_do_not_consume_an_attempt(self):
        game = MastermindSession(lambda: SECRET)
        before = game.view
        for code in ((), ("red",) * 3, ("red",) * 5, ("black",) * 4):
            with self.assertRaises(ValueError):
                game.submit(code)
            self.assertIs(game.view, before)
        self.assertEqual(game.score.games, 0)

    def test_secret_is_fixed_and_absent_from_live_views(self):
        game = MastermindSession(lambda: SECRET)
        self.assertEqual(game.code_view(), (None,) * 4)
        with self.assertRaises(ValueError):
            game.code_view(1)
        for _ in range(3):
            self.assertEqual(game.submit(MISS).feedback, Feedback(0, 0))
            self.assertEqual(game.code_view(), (None,) * 4)
        self.assertNotIn("green", repr(game.view))

    def test_all_ten_feedbacks_use_one_secret_and_only_next_round_generates_again(self):
        following = ('purple',) * 4
        factory = Mock(side_effect=[SECRET, following])
        game = MastermindSession(factory)
        guesses = [
            (('white',) * 4, Feedback(0, 0)),
            (('red',) * 4, Feedback(2, 0)),
            (('blue',) * 4, Feedback(1, 0)),
            (('green',) * 4, Feedback(1, 0)),
            (('yellow',) * 4, Feedback(0, 0)),
            (('purple',) * 4, Feedback(0, 0)),
            (('red', 'blue', 'red', 'green'), Feedback(2, 2)),
            (('green', 'blue', 'red', 'red'), Feedback(0, 4)),
            (('red', 'green', 'blue', 'red'), Feedback(2, 2)),
            (('green', 'red', 'red', 'blue'), Feedback(1, 3)),
        ]
        for index, (guess, expected) in enumerate(guesses):
            self.assertEqual(game.submit(guess).feedback, expected)
            factory.assert_called_once_with()
            if index < 9:
                with self.assertRaises(ValueError):
                    game.code_view(4)
        self.assertEqual(game.code_view(4), SECRET)
        game.settle()
        game.next_round()
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(game.code_view(), (None,) * 4)
        self.assertEqual(game.submit(following).feedback, Feedback(4, 0))

    def test_tenth_correct_guess_wins_before_exhaustion(self):
        game = MastermindSession(lambda: SECRET)
        for _ in range(9):
            game.submit(MISS)
        game.submit(SECRET)
        self.assertEqual(game.view.result, "win")
        game.settle()
        self.assertEqual((game.score.wins, game.score.losses), (1, 0))
        with self.assertRaises(ValueError):
            game.settle()
        self.assertEqual(game.code_view(2), ("red", "red", None, None))
        self.assertEqual(game.code_view(4), SECRET)

    def test_ten_misses_end_round_and_reject_further_guesses(self):
        game = MastermindSession(lambda: SECRET)
        for _ in range(10):
            game.submit(MISS)
        self.assertEqual(game.view.result, "loss")
        with self.assertRaises(ValueError):
            game.submit(SECRET)
        game.settle()
        self.assertEqual(game.score.losses, 1)
        game.next_round()
        self.assertFalse(game.view.guesses)
        self.assertEqual(game.code_view(), (None,) * 4)

    def test_repeated_colors_and_incomplete_close_are_supported(self):
        game = MastermindSession(lambda: ("purple",) * 4)
        with self.assertRaises(ValueError):
            game.next_round()
        game.submit(MISS)
        game.cancel()
        self.assertEqual(game.score.games, 0)
        with self.assertRaises(ValueError):
            game.submit(("purple",) * 4)
