"""UI status and snack contracts have a canonical view-model owner."""

import unittest

from aiko_pet.ui.view_models.contracts import StatusSnapshot
from aiko_pet.ui.view_models.food_models import FoodChoice


class UiViewContractOwnerTests(unittest.TestCase):
    def test_original_imports_retain_identity(self) -> None:
        self.assertEqual(
            StatusSnapshot.__module__, "aiko_pet.ui.view_models.contracts",
        )
        self.assertEqual(
            FoodChoice.__module__, "aiko_pet.ui.view_models.food_models",
        )
