"""The hover view operates with no DesktopPet, game or monitor references."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.application.read_snapshot import snapshot_pet

from aiko_pet.presentation.projections import project_hover
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.action_toolbar import ActionToolbar
from aiko_pet.ui.hover_contracts import HoverActions, HoverAnchor


class IndependentHoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            probe = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("Tk display unavailable") from error
        probe.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.state = PetState()
        self.anchor = HoverAnchor(300, 500, 128, 208, None, None)
        self.events: list[str] = []
        self.positions: list[tuple[int | None, int | None]] = []

        def save(x: int | None, y: int | None) -> None:
            self.positions.append((x, y))
            self.anchor = HoverAnchor(300, 500, 128, 208, x, y)

        self.panel = ActionToolbar(
            self.root,
            snapshot=lambda: project_hover(
                snapshot_pet(self.state), context_at(1_781_000_000),
                ComputerSnapshot(cpu=42), observe_computer=True,
            ),
            anchor=lambda: self.anchor,
            actions=HoverActions(
                interact=self.events.append,
                open_status=lambda: self.events.append("status"),
                open_settings=lambda _x, _y: self.events.append("settings"),
                save_position=save,
                move_speech=lambda: None,
                restore_stack=lambda: True,
            ),
            always_on_top=False,
        )
        self.addCleanup(self.root.destroy)

    def test_buttons_only_call_narrow_application_ports(self) -> None:
        self.assertFalse(hasattr(self.panel, "pet"))
        self.panel.buttons["pet"].invoke()
        self.panel.buttons["talk"].invoke()
        self.panel.settings_button.invoke()
        self.assertEqual(self.events, ["pet", "talk", "settings"])

    def test_rendering_updates_from_snapshot_not_game_object(self) -> None:
        self.state.energy = 14
        self.panel.refresh()
        self.assertIn("14%", self.panel.needs["energy"][2].cget("text"))
        self.assertIn("CPU 42 %", self.panel.hardware.cget("text"))

    def test_saved_drag_and_reset_flow_through_callback(self) -> None:
        self.panel._last_placement = (25, 35, 330, 205)
        self.panel._drag_origin = (1, 2, 3, 4)
        self.panel._drag_end(tk.Event())
        self.assertEqual(self.positions[-1], (25, 35))
        self.panel.reset_position()
        self.assertEqual(self.positions[-1], (None, None))


if __name__ == "__main__":
    unittest.main()
