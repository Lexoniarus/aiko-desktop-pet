"""World dragging survives body-pose presentation and transient frame failures."""

from __future__ import annotations

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.world.contracts import ObjectState
from tools.desktop_test_support import create_test_desktop


class WorldDragRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
            root.update_idletasks()
            root.destroy()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error)) from error

    def setUp(self) -> None:
        folder = tempfile.TemporaryDirectory(prefix="aiko-drag-regression-")
        self.addCleanup(folder.cleanup)
        self.app = create_test_desktop(
            store=StateStore(Path(folder.name) / "state.json")
        )
        self.addCleanup(self.app.quit)
        self.app._runtime.stop()
        self.app.root.update_idletasks()
        self.world = self.app._world
        self.cancel_frame()

    def cancel_frame(self) -> None:
        if self.world._timer is not None:
            self.app.root.after_cancel(self.world._timer)
            self.world._timer = None

    def test_drag_and_release_work_during_every_body_clip(self) -> None:
        track = self.world._track()
        pointer = [track.left + 180, track.ground_y - 200]
        with (
            patch.object(
                self.app.root, "winfo_pointerx", side_effect=lambda: pointer[0]
            ),
            patch.object(
                self.app.root, "winfo_pointery", side_effect=lambda: pointer[1]
            ),
            patch(
                "aiko_pet.desktop.cursor_item_gesture.mouse_buttons_down_windows",
                return_value=(True, False, False),
            ),
        ):
            for name in (
                "body-turn-left",
                "body-look-left",
                "body-turn-right",
                "body-look-right",
            ):
                for item_id in ("cookie", "energy_drink", "horoscope_book"):
                    with self.subTest(body=name, item=item_id):
                        self.app._animated.frame_clock.active_key = (name, 0)
                        pointer[0] = track.left + 180
                        self.world.begin_carry(item_id)
                        token = self.world.cursor.instance_id
                        assert token is not None
                        pointer[0] += 100
                        self.world._frame()
                        self.assertIsNotNone(self.world._timer)
                        self.cancel_frame()
                        item = self.world.world.get(token)
                        assert item.position is not None
                        sprite = self.world.view.sprite(
                            item_id, self.app.settings.scale
                        )
                        support = self.world.view.ground_pivot(
                            item_id, self.app.settings.scale
                        )
                        self.assertEqual(
                            item.position.x, 280 + support[0] - sprite.pivot[0]
                        )
                        self.assertEqual(item.state, ObjectState.USER_HELD)
                        self.world.cursor.release()
                        self.assertFalse(self.world.cursor.carrying)
                        self.assertEqual(
                            self.world.world.get(token).state, ObjectState.FALLING
                        )
                        # Dispose only fixture stock before checking the next pose.
                        item = self.world.world.get(token)
                        self.world.world.remove(token, expected_revision=item.revision)

    def test_one_render_error_does_not_kill_the_world_heartbeat(self) -> None:
        sync = self.world._sync_view
        with patch.object(
            self.world, "_sync_view", side_effect=RuntimeError("render failed")
        ):
            with self.assertRaisesRegex(RuntimeError, "render failed"):
                self.world._frame()
        self.assertIsNotNone(self.world._timer)
        self.cancel_frame()
        with patch.object(self.world, "_sync_view", wraps=sync) as rendered:
            self.world._frame()
        rendered.assert_called_once_with()
        self.assertIsNotNone(self.world._timer)
        self.cancel_frame()
