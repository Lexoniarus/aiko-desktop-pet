"""Dependency errors are detected before opening a save or constructing Tk UI."""

import unittest
from unittest.mock import Mock, patch

from aiko_pet.desktop.startup import run_desktop
from aiko_pet.infrastructure.runtime_dependencies import (
    RuntimeDependencyError,
    check_runtime_dependencies,
)


class RuntimeDependencyTests(unittest.TestCase):
    def test_real_installed_engine_computes_all_required_values(self):
        check_runtime_dependencies()

    def test_missing_or_incomplete_engine_explains_the_actual_interpreter(self):
        for failure in (ModuleNotFoundError("astronomy"), AttributeError("Time")):
            with self.subTest(failure=failure), patch(
                "aiko_pet.infrastructure.runtime_dependencies.import_module",
                side_effect=failure,
            ):
                with self.assertRaises(RuntimeDependencyError) as raised:
                    check_runtime_dependencies()
                self.assertIn("Aiko_installieren.bat", str(raised.exception))
                self.assertIn(".venv", str(raised.exception))
                self.assertIs(raised.exception.__cause__, failure)

    def test_failed_dependency_check_never_opens_the_application(self):
        create = Mock()
        with patch("aiko_pet.desktop.startup.check_runtime_dependencies",
                   side_effect=RuntimeDependencyError("missing")), patch(
                       "aiko_pet.desktop.startup.messagebox.showerror") as report:
            with self.assertRaises(SystemExit) as raised:
                run_desktop(create)
        self.assertEqual(raised.exception.code, 1)
        create.assert_not_called()
        report.assert_called_once()
