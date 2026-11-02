"""Desktop composition consumes checked resources before touching session state."""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.social_content import PreparedSocialContent, SocialCategory
from aiko_pet.gui import DesktopPet, main
from aiko_pet.infrastructure.local_jokes import load_local_jokes
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.infrastructure.runtime_dependencies import RuntimeDependencyError
from tools.desktop_test_support import create_test_desktop
from tools.tk_test_time import ControlledTkTime


class StartupResourceTests(unittest.TestCase):
    def test_main_reports_review_failure_without_opening_existing_save(self):
        with tempfile.TemporaryDirectory() as folder:
            save = Path(folder) / "existing.json"
            before = b'{"existing":"progress"}'
            save.write_bytes(before)
            with (
                patch.dict("os.environ", {"AIKO_SAVE_PATH": str(save)}),
                patch("aiko_pet.gui.load_env_file"),
                patch("aiko_pet.infrastructure.local_jokes.REVIEW_PATH",
                      Path(folder) / "missing.json"),
                patch("aiko_pet.gui.StateStore") as store,
                patch("aiko_pet.gui.PetSessionRestorer") as restore,
                patch("aiko_pet.gui.DesktopWindow") as window,
                patch("aiko_pet.desktop.startup.messagebox.showerror") as report,
                self.assertRaises(SystemExit) as stopped,
            ):
                main()
            self.assertEqual(stopped.exception.code, 1)
            store.assert_not_called()
            restore.assert_not_called()
            window.assert_not_called()
            report.assert_called_once()
            self.assertIn("Projektdateien", report.call_args.args[1])
            self.assertEqual(save.read_bytes(), before)
            self.assertFalse(save.with_suffix(".sqlite3").exists())

    def test_direct_constructor_rejects_missing_review_before_store_or_window(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "aiko_pet.infrastructure.local_jokes.REVIEW_PATH",
            Path(folder) / "missing.json",
        ), patch("aiko_pet.gui.StateStore") as store, patch(
            "aiko_pet.gui.PetSessionRestorer",
        ) as restore, patch("aiko_pet.gui.DesktopWindow") as window:
            with self.assertRaises(RuntimeDependencyError):
                DesktopPet()
        store.assert_not_called()
        restore.assert_not_called()
        window.assert_not_called()


class NativeStartupResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(str(error)) from error
        root.destroy()

    def test_main_loads_catalogue_once_and_composes_with_the_same_content(self):
        loaded: list[tuple[PreparedSocialContent, ...]] = []
        pets: list[DesktopPet] = []

        def load():
            contents = load_local_jokes()
            loaded.append(contents)
            return contents

        with tempfile.TemporaryDirectory() as folder, ControlledTkTime():
            store = StateStore(Path(folder) / "startup.sqlite3")

            def create(*, local_social_content):
                pet = create_test_desktop(
                    store=store, local_social_content=local_social_content,
                )
                pets.append(pet)
                return pet

            try:
                with (
                    patch("aiko_pet.gui.load_env_file"),
                    patch("aiko_pet.infrastructure.runtime_dependencies.load_local_jokes",
                          side_effect=load) as loader,
                    patch("aiko_pet.gui.DesktopPet", side_effect=create) as constructor,
                    patch("aiko_pet.gui.prepare_runtime_resources") as fallback,
                    patch.object(DesktopPet, "run") as run,
                ):
                    main()
                loader.assert_called_once_with()
                fallback.assert_not_called()
                constructor.assert_called_once_with(local_social_content=loaded[0])
                self.assertIs(constructor.call_args.kwargs["local_social_content"],
                              loaded[0])
                run.assert_called_once_with()
                self.assertEqual(len(pets), 1)
                content = pets[0]._social_runtime.content
                self.assertEqual(len(content.local_candidates(SocialCategory.SINGLE)),
                                 4)
                self.assertEqual(len(content.local_candidates(SocialCategory.TWO_PARTS)),
                                 13)
            finally:
                for pet in pets:
                    pet.quit()
