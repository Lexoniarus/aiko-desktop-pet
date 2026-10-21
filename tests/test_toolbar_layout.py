"""Headless placement and idle-delivery ordering, without native windows/input."""

import unittest
from collections import deque
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime
from aiko_pet.pet.animation.character import PlaybackEvent
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.contracts import HoverAnchor
from aiko_pet.ui.view_models.projections import project_hover
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.hover_contracts import HoverActions
from aiko_pet.ui.windows.hover_geometry import HoverGeometry
from tools.headless_widgets import Skin, Widget, widgets
from tools.reaction_test_support import FakeScheduler


class ToolbarLayoutTests(unittest.TestCase):
    def setUp(self):
        context = widgets()
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        self.root = Widget()
        self.anchor = HoverAnchor(1850, 1000, 128, 208, None, None)
        self.view = project_hover(snapshot_pet(PetState()), context_at(1800000000),
                                  ComputerSnapshot(), observe_computer=False)
        self.toolbar = ActionToolbar(
            cast(Any, self.root), snapshot=lambda: self.view,
            anchor=lambda: self.anchor,
            actions=HoverActions(Mock(), Mock(), Mock(), Mock(), Mock(), lambda: True),
            always_on_top=True, skin=cast(Any, Skin()),
        )
        self.addCleanup(self.toolbar.close)

    def test_refresh_does_not_deliver_pending_world_events_inside_presentation(self):
        self.toolbar.show()
        scheduler = FakeScheduler()
        world = DesktopWorldRuntime.__new__(DesktopWorldRuntime)
        world._closed, world._event_timer = False, None
        world._events = deque()
        world.root = cast(Any, Mock(after_idle=lambda cb: scheduler.schedule(0, cb)))
        world.interaction = cast(Any, Mock())
        event = PlaybackEvent(1, "pick_up", 7, finished=True)
        world._queue_event(event)
        token = world._event_timer
        assert token is not None

        def drain_idle():
            for queued in tuple(scheduler.callbacks):
                scheduler.fire(queued)

        with patch.object(self.toolbar.window, "update_idletasks", drain_idle):
            self.toolbar.refresh()
        cast(Any, world.interaction).receive.assert_not_called()
        self.assertEqual(tuple(world._events), (event,))
        scheduler.fire(token)
        cast(Any, world.interaction).receive.assert_called_once_with(event)

    def test_settled_window_resize_repositions_once_and_ignores_child_events(self):
        self.toolbar.show()
        window = cast(Any, self.toolbar.window)
        configure = window.bindings.get("<Configure>")
        self.assertIsNotNone(configure)
        with patch.object(window, "winfo_reqwidth", return_value=688), \
             patch.object(window, "winfo_reqheight", return_value=930), \
             patch.object(window, "geometry") as geometry:
            configure(Mock(widget=self.toolbar.today))
            geometry.assert_not_called()
            configure(Mock(widget=window))
            expected = HoverGeometry.placement(self.anchor, 688, 930, 1920, 1080)
            geometry.assert_called_once_with(f"+{expected[0]}+{expected[1]}")
            configure(Mock(widget=window))
            geometry.assert_called_once()
            self.toolbar._drag.start(cast(Any, Mock(x_root=20, y_root=20)))
            configure(Mock(widget=window))
            geometry.assert_called_once()
            self.toolbar.hide()
            configure(Mock(widget=window))
            geometry.assert_called_once()

    def test_initial_show_settles_requested_size_before_mapping(self):
        window = cast(Any, self.toolbar.window)
        allocated = {"width": 1, "height": 1}

        def settle_initial_geometry():
            allocated.update(width=688, height=930)

        with patch.object(window, "update_idletasks", settle_initial_geometry), \
             patch.object(window, "winfo_reqwidth", lambda: allocated["width"]), \
             patch.object(window, "winfo_reqheight", lambda: allocated["height"]):
            self.toolbar.show()
        expected = HoverGeometry.placement(self.anchor, 688, 930, 1920, 1080)
        self.assertEqual(self.toolbar._last_placement, (*expected, 688, 930))
        self.assertTrue(self.toolbar.visible)
