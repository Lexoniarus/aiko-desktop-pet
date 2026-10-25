"""Headless requested/allocated geometry boundaries, not native Tk visual QA."""

import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.ui.common.scroll_region import ScrollRegion
from tools.headless_widgets import Skin, Widget, widgets


def requested_width(region: ScrollRegion) -> int:
    # This region packs only a left canvas and a right bar/gutter. Keep the
    # allocated viewport separate from their pack geometry requests.
    return sum(child.winfo_reqwidth()
               for child in region.frame.winfo_children() if child.winfo_ismapped())


class ScrollRegionLayoutTests(unittest.TestCase):
    def test_pointer_focus_keeps_pressed_choice_stationary_but_tab_reveals_it(self):
        for horizontal in (False, True):
            with self.subTest(horizontal=horizontal), widgets():
                region = ScrollRegion(cast(Any, Widget()), cast(Any, Skin()),
                                      width=100, height=100, horizontal=horizontal)
                target = Mock()
                target.winfo_rootx.return_value = 270
                target.winfo_rooty.return_value = 270
                target.winfo_width.return_value = 50
                target.winfo_height.return_value = 50
                cast(Any, region.body).configure(width=400, height=400)
                event = cast(Any, Mock(widget=target))
                method = "xview_moveto" if horizontal else "yview_moveto"
                position = "xview" if horizontal else "yview"
                with (
                    patch.object(region.canvas, method) as move,
                    patch.object(region.canvas, position, return_value=(0, .25)),
                ):
                    region._pointer_pressed(event)
                    region._focus_visible(event)
                    move.assert_not_called()
                    region._pointer_released(event)
                    region._focus_visible(event)
                    move.assert_called_once_with(.5)

    def test_fit_growth_does_not_change_width_before_viewport_allocation(self):
        with widgets():
            region = ScrollRegion(cast(Any, Widget()), cast(Any, Skin()),
                                  width=676, height=100, fit_content=True,
                                  autohide=True, max_height=228)
            before = requested_width(region)
            body = cast(Any, region.body)
            canvas = cast(Any, region.canvas)
            body.configure(width=640, height=160)
            with patch.object(canvas, "winfo_height", return_value=100) as allocated:
                region._content_changed(None)
                self.assertEqual(canvas.cget("height"), 160)
                self.assertEqual(requested_width(region), before)
                allocated.return_value = 160
                region._viewport_changed(cast(Any, Mock(width=676)))
                self.assertEqual(requested_width(region), before)
                self.assertFalse(region.scrollbar.winfo_ismapped())

    def test_true_overflow_and_actual_parent_clipping_still_scroll(self):
        with widgets():
            region = ScrollRegion(cast(Any, Widget()), cast(Any, Skin()),
                                  width=676, height=100, fit_content=True,
                                  autohide=True, max_height=228)
            before = requested_width(region)
            cast(Any, region.body).configure(width=640, height=400)
            with patch.object(region.canvas, "winfo_height", return_value=228):
                region._content_changed(None)
                self.assertEqual(int(region.canvas.cget("height")), 228)
                self.assertTrue(region.scrollbar.winfo_ismapped())
                self.assertEqual(requested_width(region), before)
                cast(Any, region.body).configure(height=160)
                region._content_changed(None)
                self.assertFalse(region.scrollbar.winfo_ismapped())
            with patch.object(region.canvas, "winfo_height", return_value=100):
                region._viewport_changed(cast(Any, Mock(width=676)))
                self.assertTrue(region.scrollbar.winfo_ismapped())
                self.assertEqual(requested_width(region), before)
                with patch.object(region.canvas, "yview_scroll") as scroll:
                    region._scroll(1)
                    scroll.assert_called_once_with(1, "units")

    def test_horizontal_overflow_remains_local_and_resets_after_removal(self):
        with widgets():
            region = ScrollRegion(cast(Any, Widget()), cast(Any, Skin()),
                                  width=620, height=100, horizontal=True,
                                  autohide=True, fit_content=True)
            cast(Any, region.body).configure(width=900, height=80)
            region._content_changed(None)
            self.assertTrue(region.scrollbar.winfo_ismapped())
            cast(Any, region.body).configure(width=300)
            with patch.object(region.canvas, "xview_moveto") as reset:
                region._content_changed(None)
                self.assertFalse(region.scrollbar.winfo_ismapped())
                reset.assert_called_once_with(0)
