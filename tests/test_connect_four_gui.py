"""Native board input, host lifecycle, packaged pieces and completed-round effects."""

import hashlib
import json
import tempfile
import unittest
from concurrent.futures import Executor, Future
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.asset_paths import CONNECT_FOUR_DIR
from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.common.window_geometry import WindowBounds
from aiko_pet.ui.windows.connect_four_window import CELL, MARGIN, ConnectFourWindow
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class ConnectFourGuiTests(unittest.TestCase):
    def setUp(self):
        self.timing = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "save.json"),
        )
        self.addCleanup(self.pet.quit)
        self.pet._runtime.stop()
        self.executor = Mock(spec=Executor)
        self.executor.submit.side_effect = self.bot_move
        self.enterContext(patch(
            "aiko_pet.ui.windows.connect_four_sequence.ThreadPoolExecutor",
            return_value=self.executor,
        ))
        self.pet._hover.open_game(GameId.CONNECT_FOUR)
        game = self.pet._hover.game_window
        assert isinstance(game, ConnectFourWindow)
        self.game = game
        self.flow = game._sequence
        assert self.flow is not None

    @staticmethod
    def bot_move(*_args):
        future = Future()
        future.set_result(0)
        return future

    def test_hover_click_drop_result_revanche_and_once_only_reward(self):
        game, flow = self.game, self.flow
        assert flow is not None
        before = self.pet.state.fun
        self.timing.advance(10)
        self.assertFalse(flow.busy)
        self.assertEqual(len(game.canvas.find_withtag("hole")), 42)
        x = MARGIN + 3 * CELL + CELL // 2
        game.canvas.event_generate("<Motion>", x=x, y=60)
        self.assertEqual(len(game.canvas.find_withtag("preview")), 2)
        for turn in range(4):
            game.canvas.event_generate("<Button-1>", x=x, y=60)
            board = flow.game.board
            game.choose(4)
            self.assertIs(flow.game.board, board)
            self.assertEqual(len(game.canvas.find_withtag("falling")), 1)
            self.assertFalse(game.canvas.find_withtag("preview"))
            self.timing.advance(2 if turn < 3 else 12)
        self.assertEqual(flow.game.score.wins, 1)
        self.assertEqual(len(game.canvas.find_withtag("winning")), 4)
        self.assertEqual(game._panel.score_labels["wins"].cget("text"), "1")
        next_button = game._panel.next_button
        assert next_button is not None
        self.assertEqual(next_button.cget("state"), "normal")
        # Round evidence accounts for elapsed needs, but awards no session reward.
        self.assertLessEqual(self.pet.state.fun, before)
        next_button.invoke()
        self.assertEqual(flow.game.board.turn, 2)
        self.assertTrue(flow.busy)
        game.close()
        after = self.pet.state.fun
        self.assertGreater(after, before)
        game.close()
        self.assertEqual(self.pet.state.fun, after)
        self.assertFalse(self.pet._animated.game_mode)
        self.assertIsNone(self.pet._hover.game_window)
        self.assertFalse(game._tokens)

    def test_system_close_during_search_cancels_and_reopens_without_reward(self):
        assert self.flow is not None
        before = self.pet.state.fun
        self.timing.advance(10)
        self.game.choose(3)
        self.timing.advance(.2)
        self.assertTrue(self.flow.busy)
        self.pet.root.tk.eval(self.game.window.protocol("WM_DELETE_WINDOW"))
        self.timing.advance(2)
        self.assertIsNone(self.flow.pending_timer)
        self.assertFalse(self.game.window.winfo_exists())
        self.assertIsNone(self.pet._hover.game_window)
        self.assertIsNone(self.pet._speech.bubble)
        self.assertEqual(self.flow.game.score.games, 0)
        self.assertLessEqual(self.pet.state.fun, before)
        self.pet._hover.open_game(GameId.CONNECT_FOUR)
        self.assertIsInstance(self.pet._hover.game_window, ConnectFourWindow)

    def test_failed_setup_releases_panel_images_and_host_admission(self):
        self.game.close()
        for target in ("ConnectFourWindow._present", "GamePanel.show"):
            with self.subTest(target=target):
                before = set(self.pet.root.winfo_children())
                with (
                    patch("aiko_pet.ui.windows.connect_four_window." + target,
                          side_effect=RuntimeError("setup failed")),
                    patch.object(self.pet.application, "complete_game") as complete,
                ):
                    with self.assertRaisesRegex(RuntimeError, "setup failed"):
                        self.pet._hover.open_game(GameId.CONNECT_FOUR)
                complete.assert_not_called()
                self.assertEqual(set(self.pet.root.winfo_children()), before)
                self.assertIsNone(self.pet._hover.game_window)
                self.assertFalse(self.pet._hover.game_open)
                self.assertFalse(self.pet._animated.game_mode)

    def test_narrow_screen_keeps_footer_visible_and_board_scrollable(self):
        self.game.close()
        game = ConnectFourWindow(
            self.pet.root, on_closed=lambda _score: None,
            speak=lambda *_args: None, animate=lambda _clip: None,
            emote=lambda *_args: None, always_on_top=False, skin=self.game.skin,
            bounds_at=lambda _x, _y: WindowBounds(0, 0, 320, 700),
        )
        self.addCleanup(game.close)
        self.pet.root.update()
        self.assertLessEqual(game.window.winfo_width(), 320)
        self.assertLessEqual(game.window.winfo_height(), 700)
        viewport = game.canvas.master.master
        assert viewport is not None
        self.assertLess(viewport.winfo_width(), game.canvas.winfo_width())
        footer = game._panel.close_button
        self.assertTrue(footer.winfo_ismapped())
        self.assertLessEqual(footer.winfo_rooty() + footer.winfo_height(),
                             game.window.winfo_rooty() + game.window.winfo_height())


class ConnectFourAssetTests(unittest.TestCase):
    def test_packaged_pieces_are_unmodified_documented_kenney_sources(self):
        provenance = json.loads((CONNECT_FOUR_DIR / "provenance.json").read_text())
        self.assertEqual(provenance["license"], "CC0-1.0")
        self.assertIn("CC0", (CONNECT_FOUR_DIR / "LICENSE.txt").read_text())
        self.assertEqual(set(provenance["files"]), {"yellow.png", "red.png"})
        for filename, entry in provenance["files"].items():
            self.assertEqual(hashlib.sha256((CONNECT_FOUR_DIR / filename).read_bytes())
                             .hexdigest(), entry["sha256"])
