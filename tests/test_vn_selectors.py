"""Real menu ownership/commands with widget doubles, never a native window."""

import unittest
from dataclasses import MISSING, fields, replace
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import SocialCategory
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.contracts import HoverAnchor
from aiko_pet.ui.view_models.food_models import FoodChoice
from aiko_pet.ui.view_models.projections import (
    project_hover,
    project_settings,
    project_status,
)
from aiko_pet.ui.windows.hover_ui import HoverUi, HoverUiPorts
from tools.headless_widgets import Skin, Widget, widgets


class EmbeddedSelectorTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(widgets())
        self.enterContext(patch("aiko_pet.ui.windows.hover_ui.AikoSkin", Skin))
        self.toplevel = self.enterContext(patch("tkinter.Toplevel", side_effect=Widget))
        self.state = PetState()
        read = snapshot_pet(self.state)
        time = context_at(1_800_000_000)
        required = {
            f.name: Mock()
            for f in fields(HoverUiPorts)
            if f.default is MISSING and f.default_factory is MISSING
        }
        self.placed: list[str] = []
        self.selected: list[SocialCategory] = []
        self.deferred: list[Any] = []
        self.allowed, self.place_allowed, self.online = True, True, False
        self.cancel = Mock()
        self.ports = replace(
            HoverUiPorts(**cast(Any, required)),
            hover_snapshot=lambda: project_hover(
                read, time, ComputerSnapshot(), observe_computer=False
            ),
            status_snapshot=lambda: project_status(
                read, time, None, ComputerSnapshot(), observe_computer=False
            ),
            settings_snapshot=lambda: project_settings(PetSettings()),
            anchor=lambda: HoverAnchor(0, 0, 128, 208, None, None),
            food_choices=(
                FoodChoice("onigiri", "Onigiri", "Mahlzeit", 20, Path("onigiri.png")),
            ),
            can_interact=lambda _a: self.allowed,
            can_place_item=lambda: self.place_allowed,
            place_item=self.placed.append,
            social_selected=self.selected.append,
            social_cancel=self.cancel,
            social_enabled=lambda: self.online,
            social_snapshot=lambda: ("Wird vorbereitet", None),
            defer_game=self.deferred.append,
        )
        self.ui = HoverUi(cast(Any, Widget()), cast(Any, Widget()), self.ports)

    def test_selectors_share_toolbar_and_stale_placement_cannot_bypass_admission(self):
        self.allowed = False
        self.ui.open_food_menu()
        menu = self.ui.food_menu
        assert menu and self.ui.toolbar
        self.assertIs(menu.frame.master, self.ui.toolbar.interaction_column)
        self.assertFalse(hasattr(menu, "window"))
        self.assertFalse(self.ui.toolbar.actions_frame.winfo_ismapped())
        self.place_allowed = False
        menu.choose("onigiri")
        self.assertFalse(self.placed)
        self.place_allowed = True
        menu.choose("onigiri")
        menu.choose("onigiri")
        self.assertEqual(self.placed, ["onigiri"])
        self.assertTrue(self.ui.toolbar.actions_frame.winfo_ismapped())
        self.assertEqual(self.toplevel.call_count, 1)

    def test_game_choice_keeps_single_pending_owner_and_cancel_rejects_late_start(self):
        self.ui.open_game_menu()
        menu = self.ui.game_menu
        assert menu
        game = next(iter(menu.buttons))
        menu.choose(game)
        menu.choose(game)
        self.assertEqual(len(self.deferred), 1)
        self.assertTrue(self.ui.game_open)
        self.ui.close_game()
        self.deferred[0]()
        self.assertFalse(self.ui.game_open)
        self.assertIsNone(self.ui.game_window)
        self.assertEqual(self.toplevel.call_count, 1)

    def test_social_opt_out_loading_back_and_single_window_switching(self):
        self.ui.open_food_menu()
        self.ui.open_game_menu()
        self.ui.open_social_menu()
        menu = self.ui.social_menu
        assert menu
        self.assertIsNone(self.ui.food_menu)
        self.assertIsNone(self.ui.game_menu)
        menu.choose(SocialCategory.SINGLE)
        self.assertFalse(self.selected)
        self.online = True
        menu.refresh()
        self.assertEqual(menu.status.cget("text"), "Wird vorbereitet")
        menu.choose(SocialCategory.SINGLE)
        self.assertEqual(self.selected, [SocialCategory.SINGLE])
        menu.back.invoke()
        self.assertIsNone(self.ui.social_menu)
        self.cancel.assert_called_once()
        self.assertEqual(self.toplevel.call_count, 1)
