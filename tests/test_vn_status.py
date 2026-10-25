"""Window-free status commands, passivity, presentation and containment checks."""

import unittest
from typing import Any, cast
from unittest.mock import Mock

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.pet.moodlet_catalog import MOODLET_CATALOG
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import ActiveWish, WishId, WishState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.common.description_tip import tip_position
from aiko_pet.ui.common.scroll_region import ScrollRegion
from aiko_pet.ui.common.status_readout import (
    StatusReadout,
    fill_geometry,
    readout_color,
)
from aiko_pet.ui.view_models.contracts import HoverAnchor
from aiko_pet.ui.view_models.emotional_text import MOODLET_ICONS, wish_description
from aiko_pet.ui.view_models.projections import project_hover, project_status
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.hover_contracts import HoverActions
from tools.headless_widgets import Skin, Widget, widgets


class VnStatusTests(unittest.TestCase):
    def test_small_real_status_changes_are_visible_without_rounding_the_state(self):
        readout = StatusReadout.__new__(StatusReadout)
        readout.label, readout.canvas = cast(Any, Mock()), cast(Any, Mock())
        readout._fill, readout._width = 1, 280
        readout._title, readout._friendship = "Sättigung", False
        readout.refresh(69.98)
        self.assertIn("69,98", readout.label.configure.call_args.kwargs["text"])
        readout._title, readout._friendship = "Freundschaft", True
        readout.refresh(56.003)
        self.assertIn("56,003", readout.label.configure.call_args.kwargs["text"])
        readout.refresh(56)
        self.assertIn("56 / 100", readout.label.configure.call_args.kwargs["text"])

    def test_colors_and_fill_keep_zero_full_and_friendship_meaning(
        self,
    ):
        self.assertEqual(readout_color(100), "#8EBD9C")
        self.assertEqual(readout_color(50), "#E0CD86")
        self.assertEqual(readout_color(25), "#E5B080")
        self.assertEqual(readout_color(0), "#D98897")
        self.assertEqual(readout_color(0, friendship=True), "#94B5CF")
        self.assertEqual(readout_color(100, friendship=True), "#94B5CF")
        for amount in (0, 0.01, 25, 50, 100):
            points = fill_geometry(amount, 280)
            self.assertGreaterEqual(min(points[::2]), 2)
            self.assertLessEqual(max(points[::2]), 278)
        self.assertEqual(max(fill_geometry(0, 280)[::2]), 2)
        self.assertEqual(max(fill_geometry(100, 280)[::2]), 278)

    def test_description_position_stays_inside_window_and_avoids_explained_row(self):
        self.assertEqual(tip_position(600, 100, 150, 300, 100, 680, 800), (380, 154))
        self.assertEqual(tip_position(20, 700, 750, 300, 100, 680, 800), (20, 596))

    def test_focus_reveals_overflow_without_a_global_input_hook(self):
        region = ScrollRegion.__new__(ScrollRegion)
        canvas, body, target = Mock(), Mock(), Mock()
        region.canvas, region.body = cast(Any, canvas), cast(Any, body)
        region._horizontal = True
        region._pointer_focus = None
        canvas.winfo_rootx.return_value = 0
        canvas.winfo_width.return_value = 100
        canvas.xview.return_value = (0, 0.25)
        body.winfo_reqwidth.return_value = 400
        target.winfo_rootx.return_value = 250
        target.winfo_width.return_value = 50
        region._focus_visible(cast(Any, Mock(widget=target)))
        canvas.xview_moveto.assert_called_once_with(0.5)
        target.focus_set.assert_not_called()

    def test_refresh_keeps_identity_and_placement_admission(
        self,
    ):
        episodes = tuple(
            MoodletEpisode(i, key, 1, 0, 0, 7200)
            for i, key in enumerate(MOODLET_CATALOG.definitions, 1)
        )
        state = PetState(
            sleeping=True,
            mood=33,
            friendship=71,
            moodlets=MoodletState(active=episodes),
            wishes=WishState(active=(ActiveWish(1, WishId.FACT, "fact", 0, 14400),)),
        )
        before = state.capture_checkpoint()
        context = context_at(1_800_000_000)

        def hover():
            return project_hover(
                snapshot_pet(state), context, ComputerSnapshot(), observe_computer=False
            )

        def status():
            return project_status(
                snapshot_pet(state),
                context,
                None,
                ComputerSnapshot(),
                observe_computer=False,
            )

        calls: list[str] = []
        actions = HoverActions(
            calls.append,
            Mock(),
            Mock(),
            Mock(),
            Mock(),
            lambda: True,
            can_interact=lambda _a: False,
        )
        with widgets():
            toolbar = ActionToolbar(
                cast(Any, Widget()),
                snapshot=hover,
                status_snapshot=status,
                anchor=lambda: HoverAnchor(0, 0, 128, 208, None, None),
                actions=actions,
                always_on_top=True,
                skin=cast(Any, Skin()),
            )
            toolbar.refresh()
            self.assertEqual(len(toolbar.readouts), 7)
            self.assertIn("33 / 100", toolbar.readouts["mood"].label.cget("text"))
            self.assertIn("Lv 8", toolbar.readouts["friendship"].label.cget("text"))
            cards = toolbar.moodlets._scroll.body.winfo_children()
            self.assertEqual(len(cards), len(MOODLET_CATALOG.definitions))
            toolbar.refresh()
            self.assertEqual(toolbar.moodlets._scroll.body.winfo_children(), cards)
            toolbar.buttons["pet"].invoke()
            toolbar.buttons["place_item"].invoke()
            self.assertEqual(calls, ["place_item"])
            toolbar.set_pinned(True)
            self.assertTrue(toolbar.pin_button.cget("selected"))
            self.assertEqual(toolbar.pin_button.cget("text"), "")
            self.assertEqual(toolbar.settings_button.cget("text"), "")
            self.assertEqual(toolbar.pin_button.cget("size"), "small")
            self.assertEqual(toolbar.settings_button.cget("size"), "small")
            self.assertFalse(toolbar.pin_button.cget("align_left"))
            self.assertIs(toolbar.pin_button.master, toolbar.settings_button.master)
            title = cast(Any, toolbar.today).master
            self.assertIs(toolbar._drag._handle, title)
            for handle in (title, cast(Any, toolbar.today)):
                self.assertIn("<B1-Motion>", handle.bindings)
            moved = cast(Mock, actions.move_speech)
            saved = cast(Mock, actions.save_position)
            toolbar._drag.start(cast(Any, Mock(x_root=30, y_root=30)))
            toolbar._drag.move(cast(Any, Mock(x_root=40, y_root=50)))
            toolbar._drag.finish(cast(Any, Mock()))
            saved.assert_called_once_with(30, 40)
            moved.assert_called_once()
            # Descriptions are in-window and keyboard focusable, no new window.
            cast(Any, toolbar.settings_button).bindings["<FocusIn>"](Mock())
            self.assertIn("Einstellungen", toolbar.tips._label.cget("text"))
            toolbar.toggle_details()
            self.assertTrue(toolbar.details and toolbar.details.frame.winfo_ismapped())
            toolbar.close()
        self.assertEqual(state.capture_checkpoint(), before)

    def test_each_supported_wish_has_a_readable_target_objective_and_art_mapping(self):
        self.assertEqual(set(MOODLET_ICONS), set(MOODLET_CATALOG.definitions))
        for key, definition in WISH_CATALOG.definitions.items():
            state = PetState(
                wishes=WishState(
                active=(ActiveWish(1, key, definition.targets[0], 0, 14400,
                                   goal=definition.goal),)
                )
            )
            view = project_hover(
                snapshot_pet(state),
                context_at(1_800_000_000),
                ComputerSnapshot(),
                observe_computer=False,
            )
            self.assertIn(
                view.emotional.wishes[0].target_label,
                wish_description(view.emotional.wishes[0]),
            )
