"""Actual game host, concealed desktop strip, native input and safe teardown."""

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from aiko_pet.asset_paths import MASTERMIND_DIR
from aiko_pet.games.contracts import GameId
from aiko_pet.games.mastermind import COLORS, MastermindSession
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.common.window_geometry import WindowBounds
from aiko_pet.ui.view_models.game_models import HandAnchor
from aiko_pet.ui.view_models.mastermind_models import place_code
from aiko_pet.ui.windows.mastermind_window import (
    BOARD_HEIGHT,
    BOARD_PADDING,
    MastermindWindow,
)
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime

SECRET = ("red", "red", "blue", "green")


class MastermindGuiTests(unittest.TestCase):
    def test_safe_opening_and_snack_are_cosmetic_and_next_waits_for_completion(self):
        before = self.pet.state.satiety
        self.submit(SECRET)
        self.clock.advance(8)
        button = self.game._panel.next_button
        self.assertEqual(button.cget('state'), 'disabled')
        self.clock.advance(17)
        self.assertEqual(self.code._frame, 32)
        self.assertFalse(self.code._snack)
        self.assertEqual(button.cget('state'), 'normal')
        self.assertLessEqual(self.pet.state.satiety, before)
        self.assertEqual(self.game._sequence.game.score.wins, 1)

    def test_closing_during_opening_invalidates_the_safe_completion(self):
        completed = []
        self.code.open(lambda: completed.append(True))
        self.clock.advance(.5)
        self.assertGreater(self.code._frame, 0)
        self.game.close()
        self.clock.advance(4)
        self.assertEqual(completed, [])
        self.assertFalse(self.code.windows)
        self.assertIsNone(self.code._timer)

    def setUp(self):
        self.clock = self.enterContext(ControlledTkTime())
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "save.json")
        )
        self.addCleanup(self.pet.quit)
        self.pet._runtime.stop()
        self.enterContext(
            patch(
                "aiko_pet.ui.windows.mastermind_sequence.MastermindSession",
                side_effect=lambda: MastermindSession(lambda: SECRET),
            )
        )
        self.pet._hover.open_game(GameId.MASTERMIND)
        game = self.pet._hover.game_window
        assert isinstance(game, MastermindWindow)
        self.game = game
        self.code = self.pet._game_visuals.code
        self.clock.advance(10)

    def submit(self, colors):
        for slot, color in enumerate(colors):
            self.drag(color, slot)
        self.game.submit_button.invoke()

    def drag(self, color, slot, row=None, source=None):
        """Send native Tk press/motion/release with actual screen coordinates."""
        self.pet.root.update()
        board = self.game.board
        row = len(self.game._view.guesses) if row is None else row
        index = COLORS.index(color)
        widget = self.game.palette if source is None else board
        x = (
            index * self.game._palette_step + self.game._palette_step // 2
            if source is None
            else 52 + source * 48
        )
        y = (
            (18 if self.game._palette_step == 40 else 28)
            if source is None
            else 48 + row * 48
        )
        widget.event_generate("<ButtonPress-1>", x=x, y=y)
        self.pet.root.update_idletasks()
        target_x = board.winfo_rootx() + 52 + slot * 48
        target_y = board.winfo_rooty() + 48 + row * 48
        for event in ("<B1-Motion>", "<ButtonRelease-1>"):
            widget.event_generate(
                event,
                x=target_x - widget.winfo_rootx(),
                y=target_y - widget.winfo_rooty(),
                rootx=target_x,
                rooty=target_y,
            )
        self.pet.root.update_idletasks()

    def test_hidden_strip_rejects_reveal_by_hover_or_click(self):
        self.assertEqual(self.code._view.slots, (None,) * 4)
        canvas = self.code.canvas
        assert canvas is not None
        self.assertEqual(len(canvas.find_withtag("cover")), 4)
        for event in ("<Motion>", "<Button-1>", "<Button-3>"):
            canvas.event_generate(event, x=32, y=44)
        self.assertEqual(self.code._view.slots, (None,) * 4)
        self.drag("red", 0)
        self.game.submit()
        assert self.game._sequence is not None
        self.assertFalse(self.game._sequence.game.view.guesses)

    def test_input_feedback_win_reveal_revanche_and_once_only_reward(self):
        before = self.pet.state.fun
        self.submit(("red", "blue", "red", "yellow"))
        assert self.game._sequence is not None
        flow = self.game._sequence
        self.game.submit()
        self.assertEqual(len(flow.game.view.guesses), 1)
        self.clock.advance(0.37)
        fills = [
            self.game.board.itemcget(item, "fill")
            for item in self.game.board.find_withtag("feedback0")
        ]
        self.assertEqual(fills, ["#252A33", "white", "white", "#CBD3DD"])
        self.assertEqual(self.code._view.slots, (None,) * 4)
        self.clock.advance(1)
        self.submit(SECRET)
        self.clock.advance(0.37)
        self.assertEqual(flow.game.score.wins, 1)
        self.clock.advance(0.19)
        self.assertEqual(self.code._view.slots, ("red", None, None, None))
        self.clock.advance(25)
        self.assertEqual(self.code._view.slots, SECRET)
        button = self.game._panel.next_button
        assert button is not None
        self.assertEqual(button.cget("state"), "normal")
        button.invoke()
        self.assertEqual(self.code._view.slots, (None,) * 4)
        self.assertFalse(flow.game.view.guesses)
        self.game.close()
        after = self.pet.state.fun
        self.assertGreater(after, before)
        self.game.close()
        self.assertEqual(after, self.pet.state.fun)
        self.assertFalse(self.code.windows)
        self.assertFalse(self.pet._game_visuals.code_images._images)
        self.assertFalse(self.pet._animated.game_mode)

    def test_close_during_reveal_invalidates_callbacks_and_clears_stack(self):
        self.submit(SECRET)
        self.clock.advance(0.37)
        flow = self.game._sequence
        assert flow is not None
        self.pet.root.tk.eval(self.game.window.protocol("WM_DELETE_WINDOW"))
        self.clock.advance(12)
        self.assertIsNone(flow.pending_timer)
        self.assertFalse(self.code.windows)
        self.assertIsNone(self.pet._hover.game_window)
        self.assertIsNone(self.pet._speech.bubble)
        self.pet._hover.open_game(GameId.MASTERMIND)
        self.assertEqual(self.code._view.slots, (None,) * 4)

    def test_failed_construction_releases_host_and_avoids_completion(self):
        self.game.close()
        before = set(self.pet.root.winfo_children())
        with (
            patch(
                "aiko_pet.ui.windows.mastermind_window.GamePanel.show",
                side_effect=RuntimeError("setup failed"),
            ),
            patch.object(self.pet.application, "complete_game") as complete,
        ):
            with self.assertRaisesRegex(RuntimeError, "setup failed"):
                self.pet._hover.open_game(GameId.MASTERMIND)
        complete.assert_not_called()
        self.assertEqual(before, set(self.pet.root.winfo_children()))
        self.assertFalse(self.code.windows)
        self.assertFalse(self.pet._hover.game_open)
        self.assertFalse(self.pet._animated.game_mode)

    def test_ten_rows_remain_scrollable_and_scale_topmost_updates_strip(self):
        for _ in range(10):
            self.submit(("white",) * 4)
            self.clock.advance(12)
        assert self.game._sequence is not None
        self.assertEqual(self.game._sequence.game.score.losses, 1)
        self.assertEqual(len(self.game.board.find_withtag("guess")), 40)
        self.game.board_scroll.canvas.yview_moveto(1)
        self.pet.root.update()
        self.assertEqual(len(self.game.board.find_withtag("row")), 10)
        assert self.code.window is not None and self.code.canvas is not None
        # Xvfb has no window manager to acknowledge the topmost state change.
        # Verify the native request and its canonical preference together.
        with patch.object(
            self.code.window, "wm_attributes", wraps=self.code.window.wm_attributes,
        ) as attrs:
            self.pet.set_topmost(False)
        attrs.assert_called_once_with("-topmost", False)
        self.assertFalse(self.pet.settings.always_on_top)
        self.assertFalse(self.pet._overlay_stack.enabled)
        self.pet.settings.scale = 2
        self.pet._game_visuals.move()
        self.pet.root.update()
        self.assertEqual(self.code.canvas.winfo_width(), 296)
        self.assertIn(self.code.window, self.pet._overlay_windows())

    def test_first_mapping_shows_all_ten_rows_when_body_has_room_without_input(self):
        self.game.close()
        game = MastermindWindow(
            self.pet.root,
            on_closed=lambda _summary: None,
            codes=self.pet._game_visuals.code_ports,
            speak=lambda *_args: None,
            animate=lambda _clip: None,
            emote=lambda *_args: None,
            always_on_top=False,
            skin=self.pet._hover._skin,
            bounds_at=lambda _x, _y: WindowBounds(0, 0, 1920, 1440),
        )
        self.addCleanup(game.close)
        # Only initial layout work; no greet, focus event, click or drag.
        self.pet.root.update_idletasks()
        self.clock.advance(0)
        self.pet.root.update_idletasks()
        outer, viewport = game._panel.scroll.canvas, game.board_scroll.canvas
        available = (outer.winfo_height() - game.board_scroll.frame.winfo_y()
                     - BOARD_PADDING)
        self.assertGreaterEqual(available, BOARD_HEIGHT)
        self.assertEqual(viewport.winfo_height(), BOARD_HEIGHT)
        self.assertEqual(len(game.board.find_withtag("row")), 10)
        self.assertLessEqual(game.board.winfo_rooty() + BOARD_HEIGHT,
                             viewport.winfo_rooty() + viewport.winfo_height())

    def test_narrow_panel_keeps_actions_and_footer_accessible(self):
        self.game.close()
        game = MastermindWindow(
            self.pet.root,
            on_closed=lambda _summary: None,
            codes=self.pet._game_visuals.code_ports,
            speak=lambda *_args: None,
            animate=lambda _clip: None,
            emote=lambda *_args: None,
            always_on_top=False,
            skin=self.game.skin,
            bounds_at=lambda _x, _y: WindowBounds(0, 0, 320, 700),
        )
        self.addCleanup(game.close)
        self.pet.root.update()
        self.assertLessEqual(game.window.winfo_width(), 320)
        self.assertLessEqual(game.window.winfo_height(), 700)
        self.assertLessEqual(
            game.submit_button.winfo_x() + game.submit_button.winfo_width(),
            game._panel.content_width,
        )
        self.assertTrue(game._panel.close_button.winfo_ismapped())
        viewport = game.board_scroll.canvas
        outer = game._panel.scroll.canvas
        self.assertLessEqual(
            viewport.winfo_rooty() + viewport.winfo_height(),
            outer.winfo_rooty() + outer.winfo_height(),
        )
        self.assertGreaterEqual(game.palette.winfo_rooty(), outer.winfo_rooty())
        game.greet()
        self.clock.advance(10)
        for _ in range(9):
            for _ in range(4):
                game.choose("white")
            game.submit()
            self.clock.advance(12)
        self.pet.root.update()
        self.assertEqual(
            game._slot_at(
                game.board.winfo_rootx() + 52, game.board.winfo_rooty() + 48 + 9 * 48
            ),
            0,
        )
        self.assertGreater(viewport.yview()[0], 0)
        self.assertEqual(outer.yview()[0], 0)
        original = self.game
        try:
            self.game = game
            self.submit(("white",) * 4)
            self.clock.advance(12)
            assert game._sequence is not None
            self.assertEqual(game._sequence.game.score.losses, 1)
        finally:
            self.game = original

    def test_prepared_rows_accept_only_current_row_and_keep_history(self):
        self.assertEqual(len(self.game.board.find_withtag("row")), 10)
        self.assertEqual(len(self.game.board.find_withtag("slot")), 40)
        self.assertEqual(len(self.game.board.find_withtag("feedback")), 40)
        if self.game._panel.scroll.canvas.winfo_height() >= 700:
            self.assertGreaterEqual(self.game.board_scroll.canvas.winfo_height(), 400)
        self.assertEqual(self.game.palette.bindtags()[0], str(self.game.palette))
        self.drag("red", 0, row=1)
        self.assertEqual(self.game._draft, [None] * 4)
        self.drag("red", 0)
        self.drag("blue", 1)
        self.drag("red", 1, source=0)
        self.assertEqual(self.game._draft, ["blue", "red", None, None])
        self.drag("red", 2)
        self.drag("red", 3)
        self.game.submit()
        self.assertEqual(len(self.game._view.guesses), 1)
        self.clock.advance(1)
        saved = self.game._view.guesses
        self.drag("green", 0, row=0)
        self.assertEqual(self.game._view.guesses, saved)
        self.assertEqual(self.game._draft, [None] * 4)
        self.drag("white", 0)
        self.assertEqual(self.game._draft, ["white", None, None, None])
        self.assertEqual(len(self.game.board.find_withtag("guess")), 4)

    def test_cancelled_drop_and_close_release_local_grab_and_ghost(self):
        palette = self.game.palette
        self.pet.root.update_idletasks()

        def begin_drag():
            palette.event_generate(
                "<ButtonPress-1>", x=32, y=28,
                rootx=palette.winfo_rootx() + 32, rooty=palette.winfo_rooty() + 28,
            )
            self.assertIsNone(self.game._drag._ghost)
            # A click only selects; the preview starts after actual movement.
            palette.event_generate(
                "<B1-Motion>", x=48, y=28,
                rootx=palette.winfo_rootx() + 48, rooty=palette.winfo_rooty() + 28,
            )

        begin_drag()
        self.assertIsNotNone(self.game._drag._ghost)
        palette.event_generate("<ButtonRelease-1>", x=-100, y=-100)
        self.assertEqual(self.game._draft, [None] * 4)
        self.assertIsNone(palette.grab_current())
        begin_drag()
        ghost = self.game._drag._ghost
        assert ghost is not None
        self.game.close()
        self.assertFalse(ghost.winfo_exists())
        self.assertIsNone(self.pet.root.grab_current())


class MastermindPlacementAndAssetsTests(unittest.TestCase):
    def test_side_switch_avoids_player_window_and_stays_inside_screen(self):
        anchor = HandAnchor(600, 600, 192, 208, 0, 0, 1600, 900, 1)
        layout = place_code(anchor, (WindowBounds(800, 300, 1400, 900),))
        self.assertLess(layout.x + 208, anchor.x)
        for x in (0, 1408):
            layout = place_code(replace(anchor, x=x), ())
            self.assertGreaterEqual(layout.x, 0)
            self.assertLessEqual(layout.x + 208, 1600)
        narrow = replace(anchor, x=20, width=192, right=320, scale=2)
        self.assertEqual(place_code(narrow, ()).scale, 1)

    def test_imports_match_originals_and_shared_pieces_are_not_duplicated(self):
        data = json.loads((MASTERMIND_DIR / "provenance.json").read_text())
        self.assertEqual(data["license"], "CC0-1.0")
        for name, entry in data["files"].items():
            self.assertEqual(
                hashlib.sha256((MASTERMIND_DIR / name).read_bytes()).hexdigest(),
                entry["sha256"],
            )
        self.assertEqual(len(list(MASTERMIND_DIR.glob("*.png"))), 5)
        self.assertFalse((MASTERMIND_DIR / "red.png").exists())
        self.assertFalse((MASTERMIND_DIR / "yellow.png").exists())
