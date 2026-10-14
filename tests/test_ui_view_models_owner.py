"""Live desktop status projections resolve to the single canonical UI owner."""

import unittest

from aiko_pet.ui.view_models.read_models import DesktopPresentation
from aiko_pet.presentation.read_models import DesktopPresentation as LegacyPresentation
from aiko_pet.ui.view_models.projections import project_hover
from aiko_pet.presentation.projections import project_hover as LegacyHover


class ViewModelsOwnerTests(unittest.TestCase):
    def test_compatibility_uses_same_implementations(self) -> None:
        self.assertIs(DesktopPresentation, LegacyPresentation)
        self.assertIs(project_hover, LegacyHover)
