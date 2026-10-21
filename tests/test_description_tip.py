"""Pointer ownership through overlapping descriptions, entirely with doubles."""

import unittest
from typing import Any, cast
from unittest.mock import Mock

from aiko_pet.ui.common.description_tip import DescriptionTip
from tools.headless_widgets import Skin, Widget, widgets


class DescriptionTipTests(unittest.TestCase):
    def setUp(self):
        context = widgets()
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        self.parent = cast(Any, Widget(width=688, height=900))
        self.pointer = [90, 210]
        self.parent.winfo_pointerx = lambda: self.pointer[0]
        self.parent.winfo_pointery = lambda: self.pointer[1]
        self.anchor = Widget(self.parent, width=42, height=42)
        self.anchor.winfo_rootx = lambda: 80
        self.anchor.winfo_rooty = lambda: 200
        self.anchor.pack()
        self.tip = DescriptionTip(cast(Any, self.parent), cast(Any, Skin()))
        self.tip.attach(cast(Any, self.anchor), lambda: "Moodlet description")
        self.tip.show(cast(Any, self.anchor), "Moodlet description")
        frame = cast(Any, self.tip._frame)
        frame.winfo_rootx = lambda: 50
        frame.winfo_rooty = lambda: 120
        frame.configure(width=420, height=300)

    def test_overlap_does_not_hide_and_reshow_the_description(self):
        # Placing the description over its anchor causes a Leave without the
        # pointer moving. Keeping ownership avoids a hide/Enter/show cycle.
        self.anchor.bindings["<Leave>"](Mock())
        self.assertTrue(self.tip._frame.winfo_ismapped())
        self.assertIs(self.tip._anchor, self.anchor)
        self.pointer[:] = [400, 350]  # Inside the description, outside the icon.
        cast(Any, self.tip._frame).bindings["<Leave>"](Mock())
        self.assertTrue(self.tip._frame.winfo_ismapped())
        self.pointer[:] = [30, 800]  # Outside both regions.
        cast(Any, self.tip._frame).bindings["<Leave>"](Mock())
        self.assertFalse(self.tip._frame.winfo_ismapped())
        self.assertIsNone(self.tip._anchor)

    def test_old_anchor_leave_does_not_close_a_newly_explained_card(self):
        other = Widget(self.parent, width=42, height=42)
        other.winfo_rootx = lambda: 500
        other.winfo_rooty = lambda: 200
        other.pack()
        self.tip.show(cast(Any, other), "Other Moodlet")
        self.pointer[:] = [510, 210]
        self.anchor.bindings["<Leave>"](Mock())
        self.assertIs(self.tip._anchor, other)
        self.assertTrue(self.tip._frame.winfo_ismapped())

    def test_keyboard_dismissal_still_closes_while_pointer_overlaps(self):
        self.anchor.bindings["<FocusOut>"](Mock())
        self.assertFalse(self.tip._frame.winfo_ismapped())
