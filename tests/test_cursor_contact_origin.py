"""Both native entry and hover polling preserve intentional contact."""

import unittest
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from aiko_pet.application.cursor_observation import CursorObservation
from aiko_pet.pet.mind.cursor_attention import CursorAttention
from aiko_pet.ui.windows.hover_ui import HoverUi


class CursorContactOriginTests(unittest.TestCase):
    def test_self_motion_remains_unintentional_until_pointer_moves(self):
        attention = CursorAttention()
        observer = CursorObservation(attention)
        attention.observe((100, 100), 10)
        self.assertFalse(observer.classify_contact((100, 100), pet_moved_at=11))
        self.assertTrue(observer.classify_contact((105, 100), pet_moved_at=11))
        attention.observe((105, 100), 12)
        self.assertTrue(observer.classify_contact((105, 100), pet_moved_at=11))

    def test_polling_does_not_open_or_register_self_contact(self):
        hover: Any = object.__new__(HoverUi)
        root = SimpleNamespace(winfo_pointerx=lambda: 100, winfo_pointery=lambda: 100)
        root.winfo_containing = lambda _x, _y: root
        hover.root = root
        hover.canvas = object()
        hover.settings_window = None
        hover.food_menu = hover.game_menu = hover.social_menu = None
        hover.toolbar = None
        hover.pointer_inside = lambda _x, _y: True
        opened, recorded = Mock(), Mock()
        hover._ports = SimpleNamespace(
            allow_sprite_hover=lambda: False,
            sprite_access=lambda _x, _y: False,
            open_sprite_hover=opened,
            record_contact=recorded,
        )
        hover.refresh_hover(20)
        opened.assert_not_called()
        recorded.assert_not_called()
        hover._ports.allow_sprite_hover = lambda: True
        hover.refresh_hover(20.1)
        opened.assert_called_once()
        recorded.assert_called_once_with(20.1)
