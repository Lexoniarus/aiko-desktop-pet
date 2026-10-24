"""Native VN game layouts and stationary player windows; no pet save is opened."""

from __future__ import annotations

import tkinter as tk
import unittest
from collections.abc import Callable
from typing import TypedDict
from unittest.mock import Mock, patch

from aiko_pet.desktop.work_area import work_area_at
from aiko_pet.games.contracts import SessionSummary
from aiko_pet.games.tic_tac_toe import Board
from aiko_pet.ui.common.playing_card_images import PlayingCardImages
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.common.window_geometry import BoundsAt, WindowBounds, beside_character
from aiko_pet.ui.windows.blackjack_window import BlackjackWindow
from aiko_pet.ui.windows.game_contracts import GameCardPorts, GameWindow
from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow
from aiko_pet.ui.windows.tic_tac_toe_window import TicTacToeWindow


class GameTestOptions(TypedDict):
    on_closed: Callable[[SessionSummary], None]
    speak: Callable[[str, int], None]
    animate: Callable[[str], None]
    always_on_top: bool
    skin: AikoSkin
    bounds_at: BoundsAt


class GamePlacementTests(unittest.TestCase):
    def test_side_choice_and_negative_monitor_origin(self) -> None:
        area = WindowBounds(-1600, 30, 0, 1000)
        self.assertEqual(
            beside_character(-300, 800, 192, 208, 548, 600, area), (-860, 400),
        )
        self.assertEqual(
            beside_character(-1500, 800, 192, 208, 548, 600, area), (-1296, 400),
        )
        self.assertEqual(area.clamp(-2000, -100, 548, 600), (-1600, 30))

    def test_non_windows_monitor_provider_preserves_fallback(self) -> None:
        fallback = WindowBounds(0, 0, 1280, 900)
        with patch('aiko_pet.desktop.work_area.sys.platform', 'linux'):
            self.assertEqual(work_area_at(100, 100, fallback), fallback)

    def test_windows_provider_reads_negative_origin_and_taskbar_inset(self) -> None:
        fallback = WindowBounds(0, 0, 1280, 900)
        native = Mock()
        native.MonitorFromPoint.return_value = 42

        def monitor_info(_handle, pointer):
            info = pointer._obj
            info.work.left, info.work.top = -1600, 40
            info.work.right, info.work.bottom = 0, 860
            return True

        native.GetMonitorInfoW.side_effect = monitor_info
        with (
            patch('aiko_pet.desktop.work_area.sys.platform', 'win32'),
            patch('ctypes.WinDLL', return_value=native, create=True),
        ):
            self.assertEqual(
                work_area_at(-800, 300, fallback), WindowBounds(-1600, 40, 0, 860),
            )

    def test_windows_provider_failure_preserves_fallback(self) -> None:
        fallback = WindowBounds(0, 0, 1280, 900)
        with (
            patch('aiko_pet.desktop.work_area.sys.platform', 'win32'),
            patch('ctypes.WinDLL', side_effect=OSError, create=True),
        ):
            self.assertEqual(work_area_at(100, 100, fallback), fallback)


class GameSurfaceLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest('Native Tk display required') from error
        self.addCleanup(self.root.destroy)
        self.root.overrideredirect(True)
        self.root.geometry('192x208+1100+650')
        self.root.update()
        self.skin = AikoSkin(self.root)
        self.area = WindowBounds(0, 0, 1360, 920)

    def make_game(self, kind: str) -> GameWindow:
        common: GameTestOptions = {
            'on_closed': Mock(), 'speak': Mock(), 'animate': Mock(),
            'always_on_top': False, 'skin': self.skin,
            'bounds_at': lambda _x, _y: self.area,
        }
        game: GameWindow
        if kind == 'rps':
            game = RockPaperScissorsWindow(
                self.root, emote=Mock(), hand=Mock(), **common,
            )
        elif kind == 'ttt':
            game = TicTacToeWindow(self.root, **common)
        else:
            game = BlackjackWindow(
                self.root, **common,
                cards=GameCardPorts(
                    PlayingCardImages(self.root), Mock(), Mock(), Mock(),
                ),
            )
        self.addCleanup(game.close)
        self.root.update()
        return game

    def test_all_games_use_the_same_left_fallback_and_keep_position(self) -> None:
        for kind in ('rps', 'ttt', 'blackjack'):
            with self.subTest(kind=kind):
                game = self.make_game(kind)
                self.assertLess(
                    game.window.winfo_x() + game.window.winfo_width(),
                    self.root.winfo_x(),
                )
                self.assertLessEqual(
                    game.window.winfo_y() + game.window.winfo_height(),
                    self.area.bottom,
                )
                game.window.geometry('+80+50')
                self.root.geometry('+300+200')
                self.root.update()
                self.assertEqual(
                    (game.window.winfo_x(), game.window.winfo_y()), (80, 50),
                )
                game.close()
                self.root.geometry('+1100+650')
                self.root.update()

    def test_square_prepared_tokens_and_round_updates_do_not_resize(self) -> None:
        game = self.make_game('ttt')
        assert isinstance(game, TicTacToeWindow)
        geometry = game.window.winfo_geometry()
        board = Board(('X', 'O', '', '', 'X', '', '', '', 'X'), 'O', 'X', (0, 4, 8))
        game._present(board, game._sequence.game.score)
        self.root.update()
        self.assertEqual(game.window.winfo_geometry(), geometry)
        for button in game.buttons:
            self.assertEqual(button.winfo_width(), button.winfo_height())
        self.assertEqual(game.buttons[0].cget('image'), str(game._tokens['X']))
        self.assertEqual(game.buttons[1].cget('image'), str(game._tokens['O']))
        self.assertEqual(game._token_labels[0].cget('image'), str(game._tokens['X']))
        self.assertTrue(game._token_labels[0].winfo_ismapped())
        game._present(Board(('',) * 9, 'X'), game._sequence.game.score)
        self.root.update()
        self.assertFalse(game._token_labels[0].winfo_ismapped())
        self.assertEqual(
            set(game._panel.score_labels), {'wins', 'losses', 'draws', 'games'},
        )

    def test_drag_clamps_to_work_area_and_does_not_bind_close_button(self) -> None:
        game = self.make_game('blackjack')
        assert isinstance(game, BlackjackWindow)
        drag = game._panel._drag
        self.assertFalse(game._panel.header_close.bind('<B1-Motion>'))
        wrap = self.skin.images.buttons.style.lookup(
            game._panel.close_button.cget('style'), 'wraplength',
        )
        self.assertGreaterEqual(int(wrap), 100)
        self.assertTrue(game._panel.title.bind('<B1-Motion>'))
        event = tk.Event()
        event.x_root = game.window.winfo_x() + 10
        event.y_root = game.window.winfo_y() + 10
        drag.start(event)
        event.x_root, event.y_root = 3000, 3000
        drag.move(event)
        drag.finish(event)
        self.root.update()
        self.assertEqual(
            game.window.winfo_y() + game.window.winfo_height(), self.area.bottom,
        )
        placed = game.window.winfo_geometry()
        game._panel.show(self.root)
        self.root.update()
        self.assertEqual(game.window.winfo_geometry(), placed)

    def test_narrow_blackjack_scrolls_full_size_cards_and_keeps_close_accessible(self):
        self.area = WindowBounds(0, 0, 420, 650)
        game = self.make_game('blackjack')
        assert isinstance(game, BlackjackWindow)
        self.assertEqual(game.player_cards.winfo_width(), 480)
        self.assertTrue(game._hand_scroll.scrollbar.winfo_ismapped())
        self.assertTrue(game._panel.close_button.winfo_ismapped())
        self.assertLessEqual(game.window.winfo_height(), self.area.height)
        self.assertLessEqual(game.window.winfo_width(), self.area.width)

    def test_narrow_boards_and_choices_keep_all_inputs_scrollable(self) -> None:
        self.area = WindowBounds(0, 0, 320, 700)
        for kind in ('ttt', 'rps'):
            game = self.make_game(kind)
            if isinstance(game, TicTacToeWindow):
                strip = game._board_scroll
            else:
                assert isinstance(game, RockPaperScissorsWindow)
                strip = game._choices_scroll
            self.assertTrue(strip.scrollbar.winfo_ismapped())
            strip.canvas.xview_moveto(1)
            self.assertGreater(strip.canvas.xview()[0], 0)
            game.close()


if __name__ == '__main__':
    unittest.main()
