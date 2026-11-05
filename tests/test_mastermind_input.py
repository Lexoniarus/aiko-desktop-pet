"""Pointer gestures and initial layout with no native windows or mouse input."""

import tkinter as tk
import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.games.mastermind import Feedback, Guess, RoundView
from aiko_pet.presentation.geometry import WindowBounds
from aiko_pet.ui.windows.game_panel import GamePanel
from aiko_pet.ui.windows.mastermind_drag import MastermindDrag
from aiko_pet.ui.windows.mastermind_window import MastermindWindow


class MastermindInputTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch(
            "aiko_pet.ui.windows.mastermind_drag.UiScale.for_widget",
            return_value=Mock(pixels=lambda value: round(value)),
        ))
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
            patch("aiko_pet.ui.windows.mastermind_drag.scaled.Label") as label,
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
            patch("aiko_pet.ui.windows.mastermind_drag.scaled.Label",
                  return_value=label),
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
            patch("aiko_pet.ui.windows.mastermind_drag.scaled.Label"),
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
        game.board.winfo_rootx.return_value = 300
        game.board.winfo_rooty.return_value = 200
        game.board.logical.side_effect = lambda value: value
        return game

    def test_real_slot_mapping_supports_repickup_swap_and_invalid_drop_cleanup(self):
        game = self.board_window()
        with (
            patch.object(game, "_refresh"), patch.object(game, "_draw_board"),
            patch("aiko_pet.ui.windows.mastermind_drag.tk.Toplevel",
                  side_effect=lambda _owner: Mock()),
            patch("aiko_pet.ui.windows.mastermind_drag.scaled.Label"),
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

    def test_slot_mapping_uses_shared_scale_and_rejects_history(self):
        game = self.board_window()
        game._view = RoundView((Guess(("red",) * 4, Feedback(1, 0)),))
        cast(Any, game.board).logical.side_effect = lambda value: value / .5
        for slot, x in enumerate((326, 350, 374, 398)):
            self.assertEqual(game._slot_at(x, 248), slot)
        self.assertIsNone(game._slot_at(326, 224))
        self.assertIsNone(game._slot_at(326, 272))

    def test_natural_scaled_dimensions_are_placed_before_first_mapping(self):
        panel = GamePanel.__new__(GamePanel)
        panel._placed, panel.width, panel._reserve_right = False, 548, 0
        panel.window, panel.skin = cast(Any, Mock()), cast(Any, Mock())
        panel.window.winfo_reqheight.return_value = 600
        panel.window.winfo_reqwidth.return_value = 300
        panel.skin.scale.pixels.return_value = 274
        panel._bounds_at = lambda _x, _y: WindowBounds(0, 0, 1920, 1080)
        root = Mock()
        root.winfo_rootx.return_value = root.winfo_rooty.return_value = 20
        root.winfo_width.return_value = root.winfo_height.return_value = 128
        panel.show(root)
        panel.window.minsize.assert_called_once_with(274, 1)
        self.assertTrue(panel.window.geometry.call_args.args[0].startswith('+'))
        panel.show(root)
        panel.window.geometry.assert_called_once()


if __name__ == "__main__":
    unittest.main()
