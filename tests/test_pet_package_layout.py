"""Canonical pet package, legacy import identity and ownership checks."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from aiko_pet import care_actions, domain, friendship, need_decay
from aiko_pet import pet_lifecycle, routine, value_rules
from aiko_pet.pet import (
    care_actions as pet_care,
    friendship as pet_friendship,
    lifecycle as pet_lifecycle_rules,
    need_decay as pet_needs,
    routine as pet_routine,
    state as pet_state,
    value_rules as pet_values,
)


ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class PetPackageTests(unittest.TestCase):
    def test_canonical_pet_class_has_one_identity(self) -> None:
        self.assertIs(domain.PetState, pet_state.PetState)
        self.assertEqual(pet_state.PetState.__module__, "aiko_pet.pet.state")
        self.assertIs(domain.TimeContext, pet_routine.TimeContext)

    def test_care_and_needs_legacy_functions_are_exact_aliases(self) -> None:
        self.assertIs(care_actions.plan_care_action, pet_care.plan_care_action)
        self.assertIs(care_actions.apply_care_action, pet_care.apply_care_action)
        self.assertIs(need_decay.calculate_need_decay,
                      pet_needs.calculate_need_decay)
        self.assertIs(need_decay.apply_need_decay, pet_needs.apply_need_decay)

    def test_friendship_and_lifecycle_names_remain_compatible(self) -> None:
        self.assertIs(friendship.CARE_PRIMARY_NEED,
                      pet_friendship.CARE_PRIMARY_NEED)
        self.assertIs(friendship.calculate_friendship_reward,
                      pet_friendship.calculate_friendship_reward)
        self.assertIs(pet_lifecycle.advance_pet_time,
                      pet_lifecycle_rules.advance_pet_time)
        self.assertIs(pet_lifecycle.apply_daily_routine,
                      pet_lifecycle_rules.apply_daily_routine)

    def test_time_and_normalization_contracts_are_shared(self) -> None:
        self.assertIs(routine.context_at, pet_routine.context_at)
        self.assertIs(routine.MEAL_NAMES, pet_routine.MEAL_NAMES)
        self.assertIs(value_rules.bounded, pet_values.bounded)
        self.assertIs(domain.bounded, pet_values.bounded)

    def test_no_legacy_module_owns_another_pet_implementation(self) -> None:
        for module in (
            "domain.py", "care_actions.py", "friendship.py",
            "need_decay.py", "pet_lifecycle.py", "routine.py",
            "value_rules.py",
        ):
            with self.subTest(module=module):
                tree = ast.parse((ROOT / module).read_text("utf-8"))
                self.assertFalse(any(
                    isinstance(node, (ast.ClassDef, ast.FunctionDef))
                    for node in tree.body
                ))

    def test_pet_package_has_no_gui_application_or_storage_import(self) -> None:
        for file in (ROOT / "pet").glob("*.py"):
            tree = ast.parse(file.read_text("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertLessEqual(
                        node.level, 1,
                        f"{file.name} must not escape the pet context",
                    )
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertFalse(
                            alias.name.startswith(("tkinter", "aiko_pet.ui")),
                        )


if __name__ == "__main__":
    unittest.main()
