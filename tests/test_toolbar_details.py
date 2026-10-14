"""Status-only copy is retained inside the care toolbar without another window."""

from __future__ import annotations

import tkinter as tk
import unittest
from dataclasses import replace

from aiko_pet.ui.view_models.contracts import StatusSnapshot
from aiko_pet.ui.common.skin import AikoSkin
from aiko_pet.ui.windows.toolbar_details import ToolbarDetails


class ToolbarDetailTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest("No Tk display") from error
        self.addCleanup(self.root.destroy)
        self.view = StatusSnapshot(
            today="Montag", next_event="Pause", hint="Gut",
            emotion="Stimmung: Gelassen", sleep_label="Schlafen",
            hardware_line="Rechnerbeobachtung deaktiviert",
            activity_line="Mein Rhythmus: ruhig", needs=(("energy", 55),),
            friendship_level=3,
        )
        self.parent = tk.Frame(self.root)
        self.parent.pack()
        self.details = ToolbarDetails(
            self.parent, AikoSkin(self.root), lambda: self.view,
        )

    def test_details_are_a_child_frame_with_no_duplicate_actions(self) -> None:
        self.details.frame.pack()
        self.details.refresh()
        self.assertIs(self.details.frame.master, self.parent)
        self.assertFalse(any(
            isinstance(child, (tk.Toplevel, tk.Button, tk.Canvas))
            for child in self.details.frame.winfo_children()
        ))
        self.assertEqual(self.details.text("hint"), "Gut")
        self.assertEqual(self.details.text("next_event"), "Pause")
        self.assertIn("Mein Rhythmus", self.details.text("activity_line"))

    def test_details_refresh_from_detached_snapshot(self) -> None:
        self.view = replace(self.view, emotion="Stimmung: Müde")
        self.details.refresh()
        self.assertEqual(self.details.text("emotion"), "Stimmung: Müde")
        self.assertFalse(hasattr(self.details, "pet"))


if __name__ == "__main__":
    unittest.main()
