"""Desktop lifecycle owner preserves timing, presentation and save ordering."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
from typing import cast

from aiko_pet.application.activity import ActivityCoordinator, TimeProgress
from aiko_pet.desktop.attention_runtime import DesktopAttentionRuntime
from aiko_pet.desktop.maintenance import DesktopMaintenance
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.desktop.session_runtime import (
    DesktopSessionRuntime, SessionRuntimePorts,
)
from aiko_pet.pet.routine import TimeContext, context_at


class DesktopSessionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = context_at(1_781_000_000.0)
        self.next_context = context_at(1_781_003_600.0)
        self.activity = MagicMock(spec=ActivityCoordinator)
        self.attention = MagicMock(spec=DesktopAttentionRuntime)
        self.maintenance = MagicMock(spec=DesktopMaintenance)
        self.persistence = MagicMock(spec=DesktopPersistence)
        self.persistence.due.return_value = False
        self.activity.advance_lifecycle.return_value = TimeProgress(
            self.next_context, period_changed=True, sleep_changed=False,
        )
        self.events: list[str] = []
        self.visible = True
        self.runtime = DesktopSessionRuntime(
            activity=cast(ActivityCoordinator, self.activity),
            attention=cast(DesktopAttentionRuntime, self.attention),
            maintenance=cast(DesktopMaintenance, self.maintenance),
            persistence=cast(DesktopPersistence, self.persistence),
            ports=SessionRuntimePorts(
                context=lambda: self.context,
                set_context=self._set_context,
                toolbar_visible=lambda: self.visible,
                refresh_toolbar=lambda: self.events.append("toolbar"),
                refresh_status=lambda: self.events.append("status"),
                refresh_settings=lambda: self.events.append("settings"),
                save=lambda: self.events.append("save"),
            ),
        )

    def _set_context(self, context: TimeContext) -> None:
        self.context = context
        self.events.append("context")

    def test_lifecycle_uses_previous_context_then_presents_new_one(self) -> None:
        self.runtime.advance_lifecycle(100.0, 1_781_003_600.0)
        self.activity.advance_lifecycle.assert_called_once_with(
            100.0, 1_781_003_600.0, context_at(1_781_000_000.0),
        )
        self.assertIs(self.context, self.next_context)
        self.attention.handle_time_progress.assert_called_once_with(
            self.activity.advance_lifecycle.return_value, 100.0,
        )
        self.assertEqual(self.events, ["context"])

    def test_refresh_keeps_ui_order_and_autosave_cadence(self) -> None:
        self.persistence.due.return_value = True
        self.runtime.refresh(100.0)
        self.assertEqual(self.events, ["toolbar", "status", "settings", "save"])
        self.maintenance.refresh_stack.assert_called_once_with(100.0)
        self.persistence.due.assert_called_once_with(100.0)

    def test_hidden_toolbar_is_not_refreshed(self) -> None:
        self.visible = False
        self.runtime.refresh(100.0)
        self.assertEqual(self.events, ["status", "settings"])

    def test_save_advances_application_before_storage(self) -> None:
        steps: list[str] = []
        self.activity.advance_state.side_effect = lambda _now: (
            steps.append("advance")
        )
        self.persistence.save.side_effect = lambda: (
            steps.append("store"), None,
        )[1]
        with patch(
            "aiko_pet.desktop.session_runtime.time.time",
            return_value=1_781_000_000.0,
        ):
            self.assertIsNone(self.runtime.save())
        self.assertEqual(steps, ["advance", "store"])
