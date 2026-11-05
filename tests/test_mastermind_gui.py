"""Actual game host, concealed desktop strip, native input and safe teardown."""

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.asset_paths import MASTERMIND_DIR
from aiko_pet.games.contracts import GameId
from aiko_pet.games.mastermind import COLORS, MastermindSession
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.common.window_geometry import WindowBounds
from aiko_pet.ui.view_models.game_models import HandAnchor
from aiko_pet.ui.view_models.mastermind_models import place_code
from aiko_pet.ui.windows.mastermind_window import (
    BOARD_HEIGHT,
    MastermindWindow,
)
from tools.desktop_test_support import create_test_desktop, destroy_test_root
from tools.tk_test_time import ControlledTkTime

SECRET = ("red", "red", "blue", "green")


class MastermindGuiTests(unittest.TestCase):
    def test_close_during_eating_drops_snack_and_pending_completion(self):
        finale = self.game._finale
        assert finale is not None
        done = Mock()
        finale.play(True, done)
        for _ in range(200):
            if self.pet._animated._game_clip == "eat":
                break
            self.clock.advance(.05)
        self.assertEqual(self.pet._animated._game_clip, "eat")
        self.clock.advance(1.4)
        self.game.close()
        self.clock.advance(10)
        done.assert_not_called()
        self.assertFalse(finale.effects._windows)
        self.assertIsNone(self.pet._animated._game_clip)

    def test_safe_opening_and_snack_are_cosmetic_and_next_waits_for_completion(self):
        before = self.pet.state.satiety
        self.submit(SECRET)
        self.clock.advance(8)
        button = self.game._panel.next_button
        assert button is not None
        self.assertEqual(button.cget('state'), 'disabled')
        self.clock.advance(17)
        self.assertEqual(self.code._frame, 32)
        self.assertFalse(self.code._snack)
        self.assert_code_strip(SECRET)
        self.assertEqual(button.cget('state'), 'normal')
        self.game.next_round()
        self.assert_code_strip((None,) * 4)
        self.assertEqual(self.secret_factory.call_count, 2)
        self.assertLessEqual(self.pet.state.satiety, before)
        assert self.game._sequence is not None
        self.assertEqual(self.game._sequence.game.score.wins, 1)

    def assert_code_strip(self, slots):
        canvas = self.game._code_strip.canvas
        self.assertTrue(canvas.winfo_ismapped())
        self.assertEqual(len(canvas.find_withtag('solution')),
                         sum(color is not None for color in slots))
        self.assertEqual(len(canvas.find_withtag('cover')), slots.count(None))
        captions = [canvas.itemcget(item, 'text')
                    for item in canvas.find_withtag('caption')]
        names = dict(red='Rot', blue='Blau', green='Grün')
        self.assertEqual(captions, [str(i + 1) if color is None else
                                   f'{i + 1}: {names[color]}'
                                   for i, color in enumerate(slots)])
        self.assertGreaterEqual(canvas.winfo_height(),
                                    self.game.skin.scale.pixels(64))
        for item in canvas.find_withtag('solution'):
            image = canvas.itemcget(item, 'image')
            self.assertEqual(int(canvas.tk.call('image', 'width', image)),
                             self.game.skin.scale.pixels(32))

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
        self.secret_factory = Mock(return_value=SECRET)
        self.enterContext(
            patch(
                "aiko_pet.ui.windows.mastermind_sequence.MastermindSession",
                side_effect=lambda: MastermindSession(self.secret_factory),
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
        factor = widget.ui_scale.factor
        widget.event_generate("<ButtonPress-1>",
                              x=round(x * factor), y=round(y * factor))
        self.pet.root.update_idletasks()
        target_x, target_y = map(round, board.screen_point(
            52 + slot * 48, 48 + row * 48,
        ))
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
        self.assert_code_strip((None,) * 4)
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
        self.assert_code_strip(('red', None, None, None))
        self.clock.advance(25)
        self.assertEqual(self.code._view.slots, SECRET)
        self.assert_code_strip(SECRET)
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

    def test_character_scale_and_topmost_update_the_code_strip(self):
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
        self.pet.toggle_scale()
        self.pet._game_visuals.move()
        self.pet.root.update()
        self.assertEqual(self.code.canvas.winfo_width(), 296)
        self.assertIn(self.code.window, self.pet._overlay_windows())

    def test_prepared_rows_accept_only_current_row_and_keep_history(self):
        self.assertEqual(len(self.game.board.find_withtag("row")), 10)
        self.assertEqual(len(self.game.board.find_withtag("slot")), 40)
        self.assertEqual(len(self.game.board.find_withtag("feedback")), 40)
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


class MastermindBoardLayoutTests(unittest.TestCase):
    def test_full_board_and_last_row_input_at_both_display_sizes(self):
        import tkinter as tk

        from aiko_pet.ui.common.mastermind_images import MastermindImages
        from aiko_pet.ui.common.skin import AikoSkin
        from aiko_pet.ui.common.ui_scale import DisplayScale, UiScale
        from aiko_pet.ui.windows.game_contracts import GameCodePorts

        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Native Tk display required") from error
        self.addCleanup(destroy_test_root, root)
        root.withdraw()
        for size in ((3840, 2160), (1920, 1080)):
            with self.subTest(size=size):
                UiScale._roots[root] = UiScale(root, DisplayScale.for_resolution(*size))
                skin = AikoSkin(root)
                game = MastermindWindow(
                    root, on_closed=Mock(),
                    codes=GameCodePorts(MastermindImages(root), Mock(), Mock(), Mock()),
                    speak=Mock(), animate=Mock(), emote=Mock(),
                    always_on_top=False, skin=skin,
                )
                try:
                    root.update()
                    self.assertEqual(len(game.board.find_withtag("row")), 10)
                    self.assertAlmostEqual(game.board.winfo_height(),
                                           BOARD_HEIGHT * skin.scale.factor, delta=1)
                    bottom = game.board.winfo_rooty() + game.board.winfo_height()
                    self.assertLessEqual(bottom, game._panel.status.winfo_rooty())
                    prepared = MastermindSession(lambda: SECRET)
                    for _ in range(9):
                        prepared.submit(("white",) * 4)
                    assert game._sequence is not None
                    game._sequence.game = prepared
                    game._present(prepared.view, prepared.score, False, 4)
                    root.update()
                    point = tuple(map(round, game.board.screen_point(52, 480)))
                    self.assertEqual(game._slot_at(*point), 0)
                    game._drop("red", None, *point)
                    self.assertEqual(game._draft[0], "red")
                    self.assertIs(game.board.ui_scale, skin.scale)
                    self.assertIs(game.palette.ui_scale, skin.scale)
                    self.assertIs(game.submit_button.ui_scale, skin.scale)
                finally:
                    game.close()
