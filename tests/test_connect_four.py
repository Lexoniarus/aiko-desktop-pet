"""Gravity, complete win rules, tactical evidence and bounded snapshot search."""

import unittest
from threading import Event
from typing import cast

from aiko_pet.games.connect_four import (
    SEARCH_NODE_LIMIT,
    Board,
    ConnectFourSession,
    choose_column,
    winning_cells,
    winning_columns,
)

DRAW = (5, 4, 0, 4, 6, 0, 6, 0, 0, 5, 3, 6, 1, 6, 4, 0, 3, 2, 3, 4, 5,
        6, 4, 1, 0, 3, 5, 2, 3, 2, 1, 1, 2, 1, 2, 3, 2, 5, 6, 1, 5, 4)
LAST_WIN = (2, 5, 5, 2, 4, 5, 1, 0, 0, 3, 5, 3, 6, 1, 4, 5, 2, 2, 0, 1, 5,
            6, 1, 1, 6, 2, 2, 4, 6, 6, 3, 3, 4, 6, 3, 4, 3, 4, 0, 0, 0, 1)


def played(columns):
    game = ConnectFourSession()
    for column in columns:
        game.play(column, game.board.turn)
    return game


class CountingCancellation(Event):
    def __init__(self):
        super().__init__()
        self.visits = 0

    def is_set(self):
        self.visits += 1
        return super().is_set()


class ConnectFourRuleTests(unittest.TestCase):
    def test_gravity_full_column_and_invalid_inputs_do_not_change_turn(self):
        game = played([0] * 6)
        self.assertEqual([game.board.cells[r * 7] for r in range(6)], [2, 1] * 3)
        before = game.board
        for column in (0, -1, 7, True, 1.5):
            with self.assertRaises(ValueError):
                # Deliberately exercise invalid runtime input.
                game.play(cast(int, column))
            self.assertIs(game.board, before)
        with self.assertRaises(ValueError):
            game.play(1, 2)
        self.assertIs(game.board, before)

    def test_horizontal_vertical_and_both_diagonals(self):
        diagonal = [0, 1, 1, 2, 4, 2, 2, 3, 4, 3, 5, 3, 3]
        for moves in ([0, 0, 1, 1, 2, 2, 3], [0, 1] * 3 + [0],
                      diagonal, [6 - c for c in diagonal]):
            with self.subTest(moves=moves):
                game = played(moves)
                self.assertEqual(game.board.winner, 1)
                self.assertGreaterEqual(len(game.board.winning_cells), 4)
                with self.assertRaises(ValueError):
                    game.play(6, game.board.turn)

    def test_longer_and_crossing_wins_keep_all_winning_cells(self):
        cells = [0] * 42
        for cell in (35, 36, 37, 38, 39, 17, 24, 31):
            cells[cell] = 1
        self.assertEqual(set(winning_cells(tuple(cells), 38)),
                         {35, 36, 37, 38, 39, 17, 24, 31})

    def test_full_board_draw_and_last_move_win_are_distinct(self):
        self.assertEqual(played(DRAW).board.winner, 0)
        self.assertEqual(played(LAST_WIN).board.winner, 2)
        self.assertTrue(all(played(DRAW).board.cells))

    def test_settlement_is_once_only_and_starters_alternate(self):
        game = played([0, 0, 1, 1, 2, 2, 3])
        game.settle()
        self.assertEqual(game.score.wins, 1)
        with self.assertRaises(ValueError):
            game.settle()
        game.next_round()
        self.assertEqual(game.board.turn, 2)
        self.assertFalse(any(game.board.cells))
        with self.assertRaises(ValueError):
            game.next_round()
        game.cancel()
        with self.assertRaises(ValueError):
            game.play(0, 2)
        self.assertEqual(game.score.games, 1)

    def test_block_evidence_requires_a_playable_winning_drop(self):
        game = played([0, 6, 1, 6, 2])
        self.assertEqual(winning_columns(game.board.cells, 1), (3,))
        self.assertTrue(game.play(3, 2).blocked_win)
        cells = [0] * 42
        for cell in (28, 29, 30):
            cells[cell] = 1
        for cell in (35, 36, 37):
            cells[cell] = 2
        self.assertEqual(winning_columns(tuple(cells), 1), ())


class ConnectFourSearchTests(unittest.TestCase):
    def test_avoids_supporting_a_floating_opponent_win(self):
        cells = [0] * 42
        for cell in (28, 29, 30, 36):
            cells[cell] = 1
        for cell in (35, 37):
            cells[cell] = 2
        board = Board(tuple(cells), turn=2)
        self.assertEqual(winning_columns(board.cells, 1), ())
        self.assertNotEqual(choose_column(board, Event()), 3)

    def test_randomness_selects_only_between_equally_winning_moves(self):
        cells = [0] * 42
        for cell in (36, 37, 38):
            cells[cell] = 2
        board = Board(tuple(cells), turn=2)
        sizes = []

        def last(size):
            sizes.append(size)
            return size - 1

        first = choose_column(board, Event(), random_index=lambda _size: 0)
        other = choose_column(board, Event(), random_index=last)
        self.assertEqual(sizes, [2])
        self.assertEqual({first, other}, {0, 4})

    def test_takes_own_immediate_win(self):
        game = played([6, 0, 6, 1, 5, 2, 5])
        self.assertEqual(choose_column(game.board, Event()), 3)

    def test_blocks_immediate_loss_and_preserves_the_live_snapshot(self):
        game = played([0, 6, 1, 6, 2])
        board = game.board
        self.assertEqual(choose_column(board, Event()), 3)
        self.assertIs(game.board, board)
        self.assertEqual(game.score.games, 0)

    def test_search_is_bounded_and_cancellable(self):
        cancellation = CountingCancellation()
        board = played([3]).board
        result = choose_column(board, cancellation, random_index=lambda _size: 0)
        self.assertIn(result, board.legal_columns)
        self.assertLessEqual(cancellation.visits, SEARCH_NODE_LIMIT)
        cancellation.set()
        with self.assertRaises(InterruptedError):
            choose_column(board, cancellation)

    def test_invalid_or_terminal_search_is_rejected(self):
        for board in (Board(), played([0, 0, 1, 1, 2, 2, 3]).board):
            with self.assertRaises(ValueError):
                choose_column(board, Event())
