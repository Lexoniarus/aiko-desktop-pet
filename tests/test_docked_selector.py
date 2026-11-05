"""Native docking, input lifetime and stable status geometry across menu changes."""

from __future__ import annotations

import tkinter as tk
import unittest
from dataclasses import replace
from typing import Any, cast
from unittest.mock import Mock, call, patch

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.frontend.geometry import WindowBounds
from aiko_pet.frontend.view_models.contracts import HoverAnchor
from aiko_pet.frontend.view_models.food_models import food_choices
from aiko_pet.frontend.view_models.projections import project_hover, project_status
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.windows.hover_ui import HoverUi, HoverUiPorts
from tools.desktop_test_support import destroy_test_root


class DockedSelectorTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Native Tk display required") from error
        self.addCleanup(destroy_test_root, self.root)
        self.root.withdraw()
        read, context = snapshot_pet(PetState()), context_at(1_800_000_000)
        self.cancel = Mock()
        self.anchor = HoverAnchor(100, 80, 128, 208, 100, 80)
        self.hover = HoverUi(
            self.root,
            tk.Canvas(self.root),
            HoverUiPorts(
                hover_snapshot=lambda: project_hover(
                    read,
                    context,
                    ComputerSnapshot(),
                    observe_computer=False,
                ),
                status_snapshot=lambda: project_status(
                    read,
                    context,
                    None,
                    ComputerSnapshot(),
                    observe_computer=False,
                ),
                settings_snapshot=Mock(),
                anchor=lambda: self.anchor,
                care=Mock(),
                open_sprite_hover=Mock(),
                save_position=Mock(),
                set_option=Mock(),
                toggle_scale=Mock(),
                forget_rhythm=Mock(),
                reset_toolbar=Mock(),
                center=Mock(),
                quit=Mock(),
                move_speech=Mock(),
                restore_stack=lambda: True,
                always_on_top=lambda: False,
                game_speech=cast(Any, Mock()),
                food_choices=food_choices(load_item_catalog()),
                place_item=Mock(),
                social_selected=Mock(),
                social_cancel=self.cancel,
            ),
        )
        self.addCleanup(self.hover.close_toolbar)
        self.hover.show_toolbar()
        bar = self.hover.toolbar
        assert bar is not None
        self.bar = bar
        self.bar._bounds_at = lambda _x, _y: WindowBounds(
            0,
            0,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        self.root.update()
        self.errors = []
        self.root.report_callback_exception = lambda _kind, error, _trace: (
            self.errors.append(error)
        )
        self.addCleanup(lambda: self.assertEqual(self.errors, []))

    def panel(self):
        panel = self.bar.selector_panel
        assert panel is not None
        return panel

    def test_repeated_switches_do_not_resize_or_unmap_status_widgets(self):
        before = self.bar.window.winfo_geometry()
        frames = {key: item.frame for key, item in self.bar.readouts.items()}
        geometry = {key: frame.winfo_geometry() for key, frame in frames.items()}
        events = []
        for frame in frames.values():
            for sequence in ("<Configure>", "<Unmap>"):
                frame.bind(sequence, lambda event: events.append(event), add="+")
        for _ in range(3):
            for action in ("place_item", "play", "talk", "talk"):
                self.bar.buttons[action].invoke()
                self.root.update()
                self.assertEqual(self.bar.window.winfo_geometry(), before)
                self.assertTrue(self.bar.actions_frame.winfo_ismapped())
                for key, frame in frames.items():
                    self.assertIs(frame, self.bar.readouts[key].frame)
                    self.assertEqual(frame.winfo_geometry(), geometry[key])
        self.assertEqual(events, [])

    def test_same_category_toggles_and_only_one_popup_survives_switching(self):
        for action, name in (("place_item", "food_menu"), ("play", "game_menu"),
                             ("talk", "social_menu")):
            self.bar.buttons[action].invoke()
            previous = self.panel().window
            self.assertTrue(getattr(self.hover, name))
            self.assertTrue(cast(Any, self.bar.buttons[action]).instate(["selected"]))
            self.bar.buttons[action].invoke()
            self.assertIsNone(getattr(self.hover, name))
            self.assertFalse(previous.winfo_exists())
            self.assertFalse(cast(Any, self.bar.buttons[action]).instate(["selected"]))
        self.hover.open_food_menu()
        previous = self.panel().window
        self.hover.open_game_menu()
        self.assertFalse(previous.winfo_exists())
        self.assertIsNone(self.hover.food_menu)
        self.assertIsNotNone(self.hover.game_menu)

    def test_popup_and_seam_belong_to_hover_and_outside_dismissal_area(self):
        self.hover.open_game_menu()
        self.root.update()
        panel = self.panel()
        self.assertIn(panel.window, self.hover.control_windows)
        for x, y in (
            (panel.window.winfo_rootx() + 5, panel.window.winfo_rooty() + 5),
            (self.bar.window.winfo_rootx() + self.bar.window.winfo_width() + 1,
             panel.window.winfo_rooty() + 5),
        ):
            self.assertTrue(self.hover.controls_inside(x, y))
            self.assertTrue(self.hover.pointer_inside(x, y))
            self.hover.dismiss_outside(x, y)
            self.assertIsNotNone(self.hover.game_menu)
        self.hover.toggle_pin()
        self.hover.dismiss_outside(-999, -999)
        self.assertIsNone(self.hover.game_menu)
        self.assertIsNone(self.bar.selector_panel)
        self.assertTrue(self.bar.visible)

    def test_docks_right_then_left_and_tracks_owner_movement(self):
        self.hover.open_game_menu()
        self.root.update()
        panel = self.panel()
        self.assertGreaterEqual(
            panel.window.winfo_rootx(),
            self.bar.window.winfo_rootx() + self.bar.window.winfo_width(),
        )
        self.anchor = replace(self.anchor, pinned_x=130, pinned_y=120)
        self.bar.place()
        self.root.update()
        self.assertEqual(self.bar.window.winfo_rootx(), 130)
        self.assertEqual(
            panel.window.winfo_rooty(), self.bar.buttons["play"].winfo_rooty()
        )
        edge = self.root.winfo_screenwidth() - self.bar.window.winfo_width() - 5
        self.anchor = replace(self.anchor, pinned_x=edge, pinned_y=120)
        self.bar.place()
        self.root.update()
        self.assertEqual(self.bar.window.winfo_rootx(), edge)
        self.assertLessEqual(
            panel.window.winfo_rootx() + panel.window.winfo_width(),
            self.bar.window.winfo_rootx(),
        )

    def test_uses_monitor_work_area_for_bottom_clamping(self):
        bottom = [self.root.winfo_screenheight()]
        self.bar._bounds_at = lambda _x, _y: WindowBounds(
            0,
            0,
            self.root.winfo_screenwidth(),
            bottom[0],
        )
        self.hover.open_game_menu()
        self.root.update()
        panel = self.panel()
        anchor_y = self.bar.buttons["play"].winfo_rooty()
        bottom[0] = anchor_y + panel.window.winfo_height() - 10
        self.assertGreater(
            panel.window.winfo_rooty() + panel.window.winfo_height(),
            bottom[0],
        )
        panel.place()
        self.root.update()
        self.assertEqual(
            panel.window.winfo_rooty() + panel.window.winfo_height(),
            bottom[0],
        )
        self.assertLess(panel.window.winfo_rooty(), anchor_y)

    def test_escape_explicitly_cancels_social_but_switching_preserves_request(self):
        self.hover.open_social_menu()
        self.hover.open_food_menu()
        self.cancel.assert_not_called()
        self.hover.open_social_menu()
        panel = self.panel()
        panel.window.focus_force()
        self.root.update()
        panel.window.event_generate("<Escape>")
        self.root.update()
        self.assertIsNone(self.hover.social_menu)
        self.assertIsNone(self.bar.selector_panel)
        self.cancel.assert_called_once()

    def test_passive_close_preserves_request_and_hiding_cleans_up_popup(self):
        self.hover.open_social_menu()
        self.hover.dismiss_passively(-999, -999)
        self.cancel.assert_not_called()
        self.assertFalse(self.bar.visible)
        self.assertIsNone(self.bar.selector_panel)
        self.hover.open_food_menu()
        popup = self.panel().window
        self.bar.hide()
        self.assertFalse(popup.winfo_exists())
        self.assertIsNone(self.hover.food_menu)
        self.root.update()

    def test_live_scale_and_topmost_changes_include_popup(self):
        self.hover.open_game_menu()
        self.root.update()
        panel = self.panel()
        with patch.object(
            panel.window, "wm_attributes", wraps=panel.window.wm_attributes
        ) as attributes:
            self.hover.set_topmost(True)
            self.hover.set_topmost(False)
        attributes.assert_has_calls([call("-topmost", True), call("-topmost", False)])
        self.bar.skin.scale.set_percent(125)
        self.root.update()
        self.assertEqual(
            panel.window.winfo_rooty(), self.bar.buttons["play"].winfo_rooty()
        )
        self.assertIs(panel.body.ui_scale, self.bar.skin.scale)

    def test_toolbar_follows_aiko_with_panel_attached(self):
        self.hover.open_game_menu()
        self.root.update()
        before = self.panel().window.winfo_rootx()
        self.anchor = replace(self.anchor, pinned_x=None, pinned_y=None)
        self.bar.place()
        self.root.update()
        before = self.panel().window.winfo_rootx()
        self.anchor = replace(self.anchor, x=self.anchor.x + 60)
        self.bar.place()
        self.root.update()
        self.assertEqual(self.panel().window.winfo_rootx() - before, 60)
        self.assertNotEqual(self.panel().window.winfo_rootx(), before)
        self.assertEqual(
            self.panel().window.winfo_rooty(), self.bar.buttons["play"].winfo_rooty()
        )

    def test_each_category_aligns_with_its_own_button(self):
        heights = []
        for action in ("place_item", "play", "talk"):
            self.bar.buttons[action].invoke()
            self.root.update()
            y = self.panel().window.winfo_rooty()
            self.assertEqual(y, self.bar.buttons[action].winfo_rooty())
            heights.append(y)
        self.assertEqual(heights, sorted(set(heights)))
