"""Pointer gestures and initial layout with no native windows or mouse input."""

import tkinter as tk
import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.games.mastermind import Feedback, Guess, RoundView
from aiko_pet.ui.common.window_geometry import WindowBounds
from aiko_pet.ui.windows.game_panel import GamePanel
from aiko_pet.ui.windows.mastermind_drag import MastermindDrag
from aiko_pet.ui.windows.mastermind_window import MastermindWindow


class MastermindInputTests(unittest.TestCase):
    def setUp(self):
        self.source, self.images = Mock(), Mock()
        self.source.tk.call.side_effect = lambda *_args: str(self.source)
        self.drop, self.click = Mock(), Mock()
        self.drag = MastermindDrag(self.images, self.drop, self.click)
        self.addCleanup(self.drag.cancel)

    def event(self, x=100, y=100):
        return cast(Any, Mock(widget=self.source, x_root=x, y_root=y))

    def test_click_selects_once_without_mapping_a_drag_window(self):
        with patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel") as ghost:
            self.drag.begin(self.event(), "red")
            self.drag.motion(self.event(102, 101))
            self.drag.release(self.event(102, 101))
            self.drag.release(self.event())
        ghost.assert_not_called()
        self.click.assert_called_once_with("red", None)
        self.drop.assert_not_called()
        self.source.grab_release.assert_called_once()

    def test_drag_displays_the_color_and_releases_before_one_drop(self):
        ghost = Mock()
        with (
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel",
                  return_value=ghost),
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Label") as label,
        ):
            self.drag.begin(self.event(), "blue", 2)
            self.drag.motion(self.event(120, 130))
            label.assert_called_once_with(
                ghost, image=self.images.get.return_value, bd=0, bg="#010203",
            )
            self.images.get.assert_called_once_with("blue")
            ghost.geometry.assert_called_once_with("+88+98")
            ghost.deiconify.assert_called_once()
            ghost.lift.assert_called_once()
            self.drag.release(self.event(210, 220))
        ghost.destroy.assert_called_once()
        self.source.grab_release.assert_called_once()
        self.drop.assert_called_once_with("blue", 2, 210, 220)
        self.click.assert_not_called()
        self.assertIsNone(self.drag._ghost)

    def test_cancel_and_failed_ghost_creation_do_not_leave_a_grab_or_edit(self):
        self.drag.begin(self.event(), "green")
        self.drag.cancel()
        self.drag.release(self.event())
        self.click.assert_not_called()
        self.drop.assert_not_called()
        self.drag.begin(self.event(), "green")
        with patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel",
                   side_effect=RuntimeError("image setup")):
            with self.assertRaisesRegex(RuntimeError, "image setup"):
                self.drag.motion(self.event(120, 120))
        self.assertIsNone(self.drag._source)
        self.assertIsNone(self.drag._ghost)

    def test_motion_and_release_over_preview_stay_with_grabbed_source(self):
        owner = Mock(master=None)
        self.source.master = owner
        self.source.winfo_toplevel.return_value = owner
        ghost = Mock()
        label = Mock(master=ghost)

        def preview(parent):
            ghost.master = parent
            return ghost

        def deliver(target, handler, x, y):
            # Tk keeps events on descendants of the grab owner, and redirects
            # events outside that subtree to the owner (including Toplevels).
            ancestor = target
            while ancestor is not None and ancestor is not self.source:
                ancestor = ancestor.master
            if ancestor is None:
                handler(self.event(x, y))

        with (
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel",
                  side_effect=preview),
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Label", return_value=label),
        ):
            self.drag.begin(self.event(), "blue")
            self.drag.motion(self.event(120, 130))
            deliver(label, self.drag.motion, 150, 160)
            ghost.geometry.assert_called_with("+118+128")
            deliver(label, self.drag.release, 210, 220)
        ghost.transient.assert_called_once_with(owner)
        ghost.destroy.assert_called_once()
        self.drop.assert_called_once_with("blue", None, 210, 220)
        self.click.assert_not_called()
        self.assertIsNone(self.drag._source)
        self.assertIsNone(self.drag._ghost)

    def test_failed_mapping_and_destroyed_source_still_dispose_preview(self):
        ghost = Mock()
        ghost.geometry.side_effect = tk.TclError("cannot position preview")
        with (
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel",
                  return_value=ghost),
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Label"),
        ):
            self.drag.begin(self.event(), "green")
            # Cancellation must still remove the preview when Tk has already
            # destroyed the source; no stale gesture may place a piece later.
            self.source.tk.call.side_effect = tk.TclError("source destroyed")
            with self.assertRaisesRegex(tk.TclError, "cannot position preview"):
                self.drag.motion(self.event(120, 130))
            self.drag.cancel()
            self.drag.release(self.event())
        ghost.destroy.assert_called_once()
        self.assertIsNone(self.drag._source)
        self.assertIsNone(self.drag._ghost)
        self.drop.assert_not_called()
        self.click.assert_not_called()

    def test_failed_grab_cannot_leave_a_pending_click_or_drop(self):
        self.source.grab_set.side_effect = tk.TclError("cannot grab source")
        with self.assertRaisesRegex(tk.TclError, "cannot grab source"):
            self.drag.begin(self.event(), "red")
        self.drag.release(self.event())
        self.assertIsNone(self.drag._source)
        self.drop.assert_not_called()
        self.click.assert_not_called()

    def window(self):
        game = MastermindWindow.__new__(MastermindWindow)
        game._closed, game._busy, game._feedback_visible = False, True, 4
        game._view = RoundView()
        draft: list[str | None] = [None] * 4
        game._draft, game._active, game._selected_color = draft, 0, None
        game._palette_step = 64
        game.palette, game.skin = cast(Any, Mock()), cast(Any, Mock())
        game._sequence = cast(Any, Mock())
        game._drag = MastermindDrag(self.images, game._drop, game._click_piece)
        self.addCleanup(game._drag.cancel)
        return game

    def test_click_color_then_slot_and_drag_both_edit_during_greeting(self):
        game = self.window()
        with (
            patch.object(game, "_refresh"), patch.object(game, "_draw_board"),
            patch.object(game, "_slot_at", return_value=2),
        ):
            game._click_piece("red", None)
            self.assertEqual(game._draft, [None] * 4)
            cast(Mock, game.palette.create_rectangle).assert_called_once()
            game._board_press(self.event())
            self.assertEqual(game._draft, [None, None, "red", None])
            # A click can replace a filled slot; dragging still moves its piece.
            game._click_piece("blue", None)
            game._board_press(self.event())
            game._drag.release(self.event())
            self.assertEqual(game._draft[2], "blue")
            game._drop("green", None, 210, 220)
            self.assertEqual(game._draft[2], "green")
            game._draft[:] = ["red"] * 4
            game.submit()
            cast(Any, game._sequence).submit.assert_not_called()
            game._feedback_visible = 2
            game._click_piece("white", None)
            game._board_press(self.event())
            game._drop("white", None, 210, 220)
            self.assertEqual(game._draft, ["red"] * 4)

    def board_window(self):
        game = self.window()
        game.board = cast(Any, Mock())
        game.board_scroll, game.board_horizontal = cast(Any, Mock()), cast(Any, Mock())
        game._panel = cast(Any, Mock())
        for widget in (game.board, game.board_scroll.canvas,
                       game.board_horizontal.canvas, game._panel.scroll.canvas):
            widget.winfo_rootx.return_value = 300
            widget.winfo_rooty.return_value = 200
            widget.winfo_width.return_value = 460
            widget.winfo_height.return_value = 200
        return game

    def test_real_slot_mapping_supports_repickup_swap_and_invalid_drop_cleanup(self):
        game = self.board_window()
        with (
            patch.object(game, "_refresh"), patch.object(game, "_draw_board"),
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel",
                  side_effect=lambda _owner: Mock()),
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Label"),
        ):
            game._drag.begin(self.event(), "red")
            game._drag.motion(self.event(352, 248))
            game._drag.release(self.event(352, 248))
            self.assertEqual(game._draft, ["red", None, None, None])

            # Pick up the placed draft pin and move it to the next empty slot.
            game._board_press(self.event(352, 248))
            game._drag.motion(self.event(400, 248))
            game._drag.release(self.event(400, 248))
            self.assertEqual(game._draft, [None, "red", None, None])
            game._drop("blue", None, 448, 248)
            game._board_press(self.event(400, 248))
            game._drag.motion(self.event(448, 248))
            game._drag.release(self.event(448, 248))
            self.assertEqual(game._draft, [None, "blue", "red", None])

            # Future rows and positions outside the view never accept a pin;
            # the source draft stays intact and the preview is always removed.
            for x, y in ((448, 296), (900, 900)):
                game._board_press(self.event(448, 248))
                game._drag.motion(self.event(x, y))
                game._drag.release(self.event(x, y))
                self.assertEqual(game._draft, [None, "blue", "red", None])
                self.assertIsNone(game._drag._source)
                self.assertIsNone(game._drag._ghost)
        self.assertFalse(game._view.guesses)

    def test_slot_mapping_respects_scrolled_active_row_and_all_viewport_clipping(self):
        game = self.board_window()
        game._view = RoundView((Guess(("red",) * 4, Feedback(1, 0)),))
        # The first row is now scrolled out; the active row occupies its old
        # screen position. Canvas-local coordinates alone would pick the past row.
        cast(Any, game.board).winfo_rooty.return_value = 152
        for slot, x in enumerate((352, 400, 448, 496)):
            self.assertEqual(game._slot_at(x, 248), slot)
        self.assertIsNone(game._slot_at(352, 200))
        self.assertIsNone(game._slot_at(352, 296))
        for viewport in (game.board_scroll.canvas, game.board_horizontal.canvas,
                         game._panel.scroll.canvas):
            cast(Any, viewport).winfo_width.return_value = 120
            self.assertIsNone(game._slot_at(448, 248))
            cast(Any, viewport).winfo_width.return_value = 460

    def test_body_is_prepared_before_the_first_mapping_and_only_once(self):
        panel = GamePanel.__new__(GamePanel)
        panel._placed, panel.width = False, 548
        panel._reserve_right = 0
        panel.window, panel.scroll = cast(Any, Mock()), cast(Any, Mock())
        panel.window.winfo_reqheight.return_value = 1000
        panel.scroll.canvas.winfo_reqheight.return_value = 740
        panel._bounds_at = lambda _x, _y: WindowBounds(0, 0, 1920, 800)
        root = Mock()
        root.winfo_rootx.return_value = root.winfo_rooty.return_value = 20
        root.winfo_width.return_value = root.winfo_height.return_value = 128
        order = Mock()
        order.attach_mock(panel.window.deiconify, "map")
        prepare = Mock()
        order.attach_mock(prepare, "prepare")
        panel.show(root, prepare_body=prepare)
        prepare.assert_called_once_with(520)
        self.assertEqual([c[0] for c in order.mock_calls], ["prepare", "map"])
        panel.show(root, prepare_body=prepare)
        prepare.assert_called_once()

    def layout_window(self):
        game = self.window()
        game._layout_timer = None
        game.window, game._panel = cast(Any, Mock()), cast(Any, Mock())
        game.board_scroll, game._codes = cast(Any, Mock()), cast(Any, Mock())
        game.board_scroll.frame.winfo_y.return_value = 200
        return game

    def test_unmapped_viewport_does_not_replace_prepared_ten_row_height(self):
        game = self.layout_window()
        viewport = cast(Mock, game._panel.scroll.canvas)
        board = cast(Mock, game.board_scroll.canvas)
        viewport.winfo_height.return_value = 1
        game._fit_board(740)
        board.configure.assert_called_once_with(height=504)
        # An early idle pass still sees Tk's unmapped one-pixel allocation.
        game._fit_board()
        board.configure.assert_called_once_with(height=504)

    def test_viewport_allocation_finishes_layout_without_click_or_window_resize(self):
        game = self.layout_window()
        viewport = cast(Mock, game._panel.scroll.canvas)
        board, window = cast(Mock, game.board_scroll.canvas), cast(Mock, game.window)
        viewport.winfo_height.return_value = 740
        callbacks = []
        window.after_idle.side_effect = lambda callback: (
            callbacks.append(callback) or "layout"
        )
        game._configured(cast(Any, Mock(widget=game._panel.scroll.canvas)))
        self.assertEqual(len(callbacks), 1)
        callbacks.pop()()
        board.configure.assert_called_once_with(height=504)
        # Genuine constrained work areas still use the available height.
        viewport.winfo_height.return_value = 430
        game._configured(cast(Any, Mock(widget=game._panel.scroll.canvas)))
        callbacks.pop()()
        self.assertEqual(board.configure.call_args.kwargs,
                         {"height": 222})

    def test_explicit_preparation_replaces_pending_idle_and_close_cancels_layout(self):
        game = self.layout_window()
        window = cast(Mock, game.window)
        window.after_idle.return_value = "old-layout"
        game._queue_layout()
        game._fit_board(740)
        window.after_cancel.assert_called_once_with("old-layout")
        self.assertIsNone(game._layout_timer)
        game._closed = True
        game._queue_layout()
        self.assertEqual(window.after_idle.call_count, 1)


if __name__ == "__main__":
    unittest.main()
