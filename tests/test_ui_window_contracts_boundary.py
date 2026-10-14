"""UI window contracts have one canonical implementation."""

import unittest

from aiko_pet.ui.windows.hover_geometry import HoverGeometry
from aiko_pet.ui.hover_geometry import HoverGeometry as LegacyHoverGeometry
from aiko_pet.ui.windows.toolbar_details import ToolbarDetails
from aiko_pet.ui.toolbar_details import ToolbarDetails as LegacyToolbarDetails


class WindowContractsBoundaryTests(unittest.TestCase):
    def test_legacy_contract_classes_are_identical(self) -> None:
        self.assertIs(HoverGeometry, LegacyHoverGeometry)
        self.assertIs(ToolbarDetails, LegacyToolbarDetails)
