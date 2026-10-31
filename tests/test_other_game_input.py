"""Real game views and command admission with native Tk entirely replaced."""

import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from test_blackjack import arranged_game, card

from aiko_pet.games.blackjack import Phase
from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.ui.windows.blackjack_window import BlackjackWindow
from aiko_pet.ui.windows.connect_four_window import CELL, MARGIN, ConnectFourWindow
from aiko_pet.ui.windows.game_contracts import GameCardPorts
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow
from aiko_pet.ui.windows.tic_tac_toe_window import TicTacToeWindow
from tools.headless_widgets import Skin, Widget, widgets


class GameWidget(Widget):
    create_text = Widget.create_window

    def delete(self, *_args):
        pass

    tag_raise = delete

    def after(self, _milliseconds, _callback):
        return "pending-game-step"


class OtherGameInputTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(widgets())
        self.enterContext(patch.multiple(
            "tkinter", Canvas=GameWidget, Button=GameWidget, Toplevel=GameWidget,
        ))
        self.enterContext(patch("tkinter.PhotoImage", return_value=Mock()))
        self.enterContext(patch(
            "aiko_pet.ui.windows.connect_four_sequence.ThreadPoolExecutor",
            return_value=Mock(),
        ))
        self.root, self.skin = cast(Any, GameWidget()), cast(Any, Skin())
        self.effects = {
            "on_closed": Mock(), "speak": Mock(), "animate": Mock(),
            "always_on_top": False, "skin": self.skin,
            "dialogue": lambda event: event,
        }

    def check_pointer_focus(self, region, widget):
        # Dispatch the installed local bindings, including the tag which must
        # precede native button focus. Native press/release itself is not emulated.
        self.assertLess(widget.bindtags().index(region._tag),
                        widget.bindtags().index("Widget"))
        event = Mock(widget=widget)
        with (
            patch.object(region.canvas, "xview_moveto") as horizontal,
            patch.object(region.canvas, "yview_moveto") as vertical,
        ):
            region.canvas.bindings[region._tag + "<ButtonPress-1>"](event)
            region.canvas.bindings[region._tag + "<FocusIn>"](event)
            region.canvas.bindings[region._tag + "<ButtonRelease-1>"](event)
        horizontal.assert_not_called()
        vertical.assert_not_called()

    def test_blackjack_first_decision_counts_and_dealer_turn_is_protected(self):
        for action in ("hit", "stand"):
            with self.subTest(action=action), patch(
                "aiko_pet.ui.windows.blackjack_sequence.Blackjack",
                side_effect=lambda: arranged_game(
                    card("5"), card("9"), card("6"), card("7"), card("2"),
                ),
            ):
                ports = GameCardPorts(Mock(), Mock(), Mock(), Mock())
                game = BlackjackWindow(self.root, cards=ports, **self.effects)
                self.addCleanup(game.close)
                game.greet()
                for _ in range(6):  # greeting, shuffle, four landing boundaries
                    game._sequence.advance()
                button = game.hit_button if action == "hit" else game.stand_button
                self.check_pointer_focus(game._panel.scroll, button)
                self.assertEqual(button.cget("state"), "normal")
                button.invoke()
                table = game._sequence.game.table
                if action == "hit":
                    self.assertEqual(len(table.player), 3)
                    game._sequence.advance()  # hit lands before the next decision
                    game.stand_button.invoke()
                else:
                    self.assertEqual(table.phase, Phase.DEALER)
                protected = game._sequence.game.table
                self.assertEqual(game.hit_button.cget("state"), "disabled")
                self.assertEqual(game.stand_button.cget("state"), "disabled")
                game.hit_button.invoke()
                game.stand_button.invoke()
                self.assertEqual(game._sequence.game.table, protected)

    def test_tic_tac_toe_first_cell_counts_and_aiko_turn_blocks_duplicate_input(self):
        game = TicTacToeWindow(self.root, **self.effects)
        self.addCleanup(game.close)
        game.greet()
        self.check_pointer_focus(game._board_scroll, game.buttons[0])
        game.buttons[0].invoke()
        board = game._sequence.game.board
        self.assertEqual(board.cells[0], "X")
        self.assertEqual(board.turn, "O")
        self.assertTrue(all(b.cget("state") == "disabled" for b in game.buttons))
        game.buttons[1].invoke()
        self.assertIs(game._sequence.game.board, board)
        game._sequence.advance()
        self.assertEqual(game._sequence.game.board.turn, "X")
        self.assertEqual(game.buttons[0].cget("state"), "disabled")

    def test_rps_first_hand_counts_and_countdown_keeps_input_disabled(self):
        game = RockPaperScissorsWindow(
            self.root, emote=Mock(), hand=Mock(), **self.effects,
        )
        self.addCleanup(game.close)
        game.greet()
        self.check_pointer_focus(game._choices_scroll, game.buttons[Move.ROCK])
        game.buttons[Move.ROCK].invoke()
        self.assertTrue(game._sequence.busy)
        self.assertTrue(all(b.cget("state") == "disabled"
                            for b in game.buttons.values()))
        game.buttons[Move.PAPER].invoke()
        self.assertTrue(game._sequence.busy)
        self.assertEqual(game.score.games, 0)
        for _ in range(7):
            game._sequence.advance()
        self.assertEqual(game.score.games, 1)
        self.assertTrue(all(b.cget("state") == "normal"
                            for b in game.buttons.values()))

    def test_connect_four_first_canvas_click_counts_and_drop_blocks_second(self):
        game = ConnectFourWindow(self.root, emote=Mock(), **self.effects)
        self.addCleanup(game.close)
        game.greet()
        canvas = cast(Any, game.canvas)
        # The innermost region owns the canvas. Outer adoption must not replace it.
        tag = next(t for t in canvas.bindtags() if t.startswith("VnScroll"))
        region_canvas = canvas.master.master
        event = Mock(widget=canvas, x=MARGIN + CELL * 3 + CELL // 2, y=60)
        region_canvas.bindings[tag + "<ButtonPress-1>"](event)
        with patch.object(canvas, "focus_set", side_effect=lambda:
                          region_canvas.bindings[tag + "<FocusIn>"](event)):
            canvas.bindings["<Button-1>"](event)
        board = game._view
        self.assertEqual(board.cells[38], 1)
        self.assertTrue(game._busy)
        canvas.bindings["<Button-1>"](event)
        self.assertIs(game._view, board)


if __name__ == "__main__":
    unittest.main()
