"""Rules, explicit completion and the small opponent, without any UI."""

import unittest

from aiko_pet.games.tic_tac_toe import LINES, Board, TicTacToe


class TicTacToeTests(unittest.TestCase):
    def test_all_winning_lines_and_no_credit_before_settle(self) -> None:
        for line in LINES:
            with self.subTest(line=line):
                game = TicTacToe()
                other = [i for i in range(9) if i not in line]
                for i in range(2):
                    game.play(line[i])
                    game.play(other[i], "O")
                game.play(line[2])
                self.assertEqual(game.board.winning_line, line)
                self.assertEqual(game.score.games, 0)
                game.settle()
                self.assertEqual(game.score.wins, 1)
                with self.assertRaises(ValueError):
                    game.settle()
                game.next_round()
                self.assertEqual(game.board.turn, "O")

    def test_draw_and_illegal_actions(self) -> None:
        game = TicTacToe()
        for i, cell in enumerate((0, 1, 2, 4, 3, 5, 7, 6, 8)):
            game.play(cell, "X" if i % 2 == 0 else "O")
        self.assertEqual(game.board.winner, "")
        game.settle()
        self.assertEqual(game.score.draws, 1)
        for action in (lambda: game.play(0), game.aiko_move):
            with self.assertRaises(ValueError):
                action()

    def test_wrong_turn_bounds_occupied_and_cancel_are_rejected(self) -> None:
        game = TicTacToe()
        for cell in (-1, 9, True):
            with self.assertRaises(ValueError):
                game.play(cell)
        with self.assertRaises(ValueError):
            game.next_round()
        game.play(0)
        with self.assertRaises(ValueError):
            game.play(1)
        with self.assertRaises(ValueError):
            game.play(0, "O")
        game.cancel()
        with self.assertRaises(ValueError):
            game.aiko_move()
        self.assertEqual(game.score.games, 0)

    def test_bot_wins_before_blocking_and_otherwise_blocks(self) -> None:
        for cells, expected in (
            (("O", "O", "", "X", "X", "", "", "", ""), 2),
            (("X", "X", "", "O", "", "", "", "", ""), 2),
            (("X", "", "", "", "", "", "", "", ""), 4),
            (("X", "", "", "", "O", "", "", "", ""), 2),
            (("X", "", "O", "", "X", "", "X", "", "O"), 5),
        ):
            game = TicTacToe(random_index=lambda _size: 0)
            game._board = Board(cells, "O")
            game.aiko_move()
            self.assertEqual(game.board.cells[expected], "O")

    def test_randomness_varies_equal_priority_choices_and_start_alternates(self):
        game = TicTacToe(random_index=lambda size: size - 1)
        game._board = Board(("", "", "", "", "X", "", "", "", ""), "O")
        game.aiko_move()
        self.assertEqual(game.board.cells[8], "O")
        for starter in ("O", "X"):
            game._board = Board(("X",) * 9, "O", "X", (0, 1, 2))
            game.settle()
            game.next_round()
            self.assertEqual(game.board.turn, starter)
