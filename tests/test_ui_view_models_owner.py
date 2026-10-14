"""Live desktop status projections resolve to the single canonical UI owner."""

import unittest

from aiko_pet.ui.view_models.read_models import DesktopPresentation
from aiko_pet.ui.view_models.projections import project_hover


class ViewModelsOwnerTests(unittest.TestCase):
    def test_compatibility_uses_same_implementations(self) -> None:
        self.assertEqual(
            DesktopPresentation.__module__,
            "aiko_pet.ui.view_models.read_models",
        )
        self.assertEqual(project_hover.__module__, "aiko_pet.ui.view_models.projections")
