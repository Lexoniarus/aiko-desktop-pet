"""UI window contracts have one canonical implementation."""

import unittest

from aiko_pet.ui.windows.hover_geometry import HoverGeometry
from aiko_pet.ui.windows.toolbar_details import ToolbarDetails


class WindowContractsBoundaryTests(unittest.TestCase):
    def test_legacy_contract_classes_are_identical(self) -> None:
        self.assertEqual(HoverGeometry.__module__, "aiko_pet.ui.windows.hover_geometry")
        self.assertEqual(ToolbarDetails.__module__, "aiko_pet.ui.windows.toolbar_details")
