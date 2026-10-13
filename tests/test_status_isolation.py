"""The status view uses snapshots and selected callbacks, not DesktopPet."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.ui.hover_contracts import HoverAnchor
from aiko_pet.ui.status_contracts import StatusActions, StatusSnapshot
from aiko_pet.ui.status_panel import StatusPanel


def snapshot() -> StatusSnapshot:
    return StatusSnapshot(
        today="Montag", next_event="Pause", hint="Gut",
        emotion="Stimmung: Gelassen", sleep_label="Schlafen",
        hardware_line="Rechnerbeobachtung deaktiviert", activity_line="",
        needs=(
            ("satiety", 65), ("mood", 75), ("energy", 55),
            ("social", 35), ("affection", 45), ("friendship", 25),
        ),
        friendship_level=3,
    )


class StandaloneStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as err:
            raise unittest.SkipTest("No display") from err
        root.destroy()

    def setUp(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.interactions: list[str] = []
        self.closed = False
        self.panel = StatusPanel(
            self.root,
            snapshot=snapshot,
            anchor=lambda: HoverAnchor(300, 500, 128, 208, None, None),
            actions=StatusActions(
                interact=self.interactions.append,
                quit=lambda: self.interactions.append("quit"),
                closed=lambda: setattr(self, "closed", True),
            ),
            always_on_top=False,
        )
        self.addCleanup(self.root.destroy)

    def test_independent_status_keeps_care_buttons(self) -> None:
        self.assertFalse(hasattr(self.panel, "pet"))
        self.assertIn("65%", self.panel.bars["satiety"][2].cget("text"))
        self.panel.sleep_button.invoke()
        self.assertEqual(self.interactions, ["sleep"])

    def test_close_uses_notifier_callback(self) -> None:
        self.panel.close()
        self.assertTrue(self.closed)


if __name__ == "__main__":
    unittest.main()
