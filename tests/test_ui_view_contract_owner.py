"""UI status and snack contracts have a canonical view-model owner."""

import unittest

from aiko_pet.ui.view_models.contracts import StatusSnapshot
from aiko_pet.presentation.contracts import StatusSnapshot as OldStatusSnapshot
from aiko_pet.ui.view_models.food_models import FoodChoice
from aiko_pet.presentation.food_models import FoodChoice as OldFoodChoice


class UiViewContractOwnerTests(unittest.TestCase):
    def test_original_imports_retain_identity(self) -> None:
        self.assertIs(StatusSnapshot, OldStatusSnapshot)
        self.assertIs(FoodChoice, OldFoodChoice)
