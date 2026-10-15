"""Pure tests for draggable hover position and sprite-to-panel bridge."""

import unittest

from aiko_pet.ui.view_models.contracts import HoverAnchor
from aiko_pet.ui.windows.hover_geometry import HoverGeometry, Rect


class HoverGeometryTests(unittest.TestCase):
    def test_default_location_uses_right_then_falls_back_left(self) -> None:
        anchor = HoverAnchor(300, 400, 128, 208, None, None)
        self.assertEqual(
            HoverGeometry.placement(anchor, 150, 100, 800, 800),
            (438, 454),
        )
        self.assertEqual(
            HoverGeometry.placement(anchor, 150, 100, 470, 800),
            (140, 454),
        )

    def test_saved_location_and_drag_clamp_to_screen(self) -> None:
        anchor = HoverAnchor(300, 400, 128, 208, 20, 30)
        self.assertEqual(
            HoverGeometry.placement(anchor, 150, 100, 800, 800),
            (20, 30),
        )
        self.assertEqual(
            HoverGeometry.dragged(
                (20, 30, 100, 80), (999, -100), (100, 80), (800, 600),
            ),
            (700, 0),
        )

    def test_pointer_crosses_narrow_gap_unless_panel_pinned(self) -> None:
        sprite = Rect(200, 400, 128, 208)
        panel = Rect(338, 420, 150, 100)
        self.assertTrue(HoverGeometry.bridge(
            334, 430, panel, sprite, pinned=False,
        ))
        self.assertFalse(HoverGeometry.bridge(
            334, 430, panel, sprite, pinned=True,
        ))
        self.assertFalse(HoverGeometry.bridge(
            500, 600, panel, sprite, pinned=False,
        ))


if __name__ == "__main__":
    unittest.main()
