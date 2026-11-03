"""Dependency errors are detected before opening a save or constructing Tk UI."""

import unittest
from dataclasses import FrozenInstanceError
from importlib import import_module
from unittest.mock import Mock, patch

from aiko_pet.desktop.startup import run_desktop
from aiko_pet.infrastructure.runtime_dependencies import (
    RuntimeDependencyError,
    check_runtime_dependencies,
    prepare_runtime_resources,
)


class RuntimeDependencyTests(unittest.TestCase):
    def test_missing_ui_image_library_is_reported_before_opening_a_session(self):
        real_import = import_module

        def missing_pillow(name):
            if name == 'PIL.Image':
                raise ModuleNotFoundError('PIL')
            return real_import(name)

        with patch('aiko_pet.infrastructure.runtime_dependencies.import_module',
                   side_effect=missing_pillow):
            with self.assertRaisesRegex(RuntimeDependencyError, 'Pillow') as raised:
                prepare_runtime_resources()
        self.assertIn('Aiko_installieren.bat', str(raised.exception))

    def test_missing_library_or_wrong_version_is_reported_before_session_creation(self):
        real_import = import_module

        def missing_library(name):
            if name == "pyjokes":
                raise ModuleNotFoundError("pyjokes")
            return real_import(name)

        for library_import, installed in ((missing_library, "0.8.3"),
                                           (real_import, "999.0")):
            with patch("aiko_pet.infrastructure.local_jokes.import_module",
                       side_effect=library_import), patch(
                "aiko_pet.infrastructure.local_jokes.version",
                return_value=installed,
            ), self.assertRaises(RuntimeDependencyError) as raised:
                check_runtime_dependencies()
            self.assertIn("pyjokes", str(raised.exception))
            self.assertIn("Aiko_installieren.bat", str(raised.exception))

    def test_real_installed_engine_computes_all_required_values(self):
        check_runtime_dependencies()

    def test_preparation_retains_the_checked_immutable_content(self):
        from aiko_pet.infrastructure.local_jokes import load_local_jokes

        contents = load_local_jokes()
        with patch("aiko_pet.infrastructure.runtime_dependencies.load_local_jokes",
                   return_value=contents) as load:
            resources = prepare_runtime_resources()
        load.assert_called_once_with()
        self.assertIs(resources.local_social_content, contents)
        self.assertEqual(len(contents), 17)
        with self.assertRaises(FrozenInstanceError):
            setattr(resources, "local_social_content", ())

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
        with patch("aiko_pet.desktop.startup.prepare_runtime_resources",
                   side_effect=RuntimeDependencyError("missing")), patch(
                       "aiko_pet.desktop.startup.messagebox.showerror") as report:
            with self.assertRaises(SystemExit) as raised:
                run_desktop(create)
        self.assertEqual(raised.exception.code, 1)
        create.assert_not_called()
        report.assert_called_once()

    def test_prepared_resources_are_passed_to_factory_before_running_app(self):
        resources = prepare_runtime_resources()
        app = Mock()
        create = Mock(return_value=app)
        with patch("aiko_pet.desktop.startup.prepare_runtime_resources",
                   return_value=resources) as prepare:
            run_desktop(create)
        prepare.assert_called_once_with()
        create.assert_called_once_with(resources)
        app.run.assert_called_once_with()
