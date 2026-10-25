"""Pointer gestures and initial layout with no native windows or mouse input."""

import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.games.mastermind import RoundView
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

    def test_body_is_prepared_before_the_first_mapping_and_only_once(self):
        panel = GamePanel.__new__(GamePanel)
        panel._placed, panel.width = False, 548
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


if __name__ == "__main__":
    unittest.main()
