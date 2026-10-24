"""Private path selection preserves legacy aliases without touching user saves."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.config import load_env_file
from aiko_pet.infrastructure.persistence import default_save_path as public_json_path
from aiko_pet.infrastructure.save_paths import (
    SavePaths,
    default_save_path,
    resolve_save_paths,
)

ROOT = Path(__file__).resolve().parents[1]


class SavePathTests(unittest.TestCase):
    def test_private_platform_defaults_create_no_directory(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            platforms = (("win32", "LOCALAPPDATA"), ("linux", "XDG_DATA_HOME"))
            for platform, variable in platforms:
                with (
                    self.subTest(platform=platform),
                    patch.dict(os.environ, {variable: folder, "AIKO_SAVE_PATH": " "}),
                    patch("aiko_pet.infrastructure.save_paths.sys.platform", platform),
                ):
                    directory = Path(folder) / "AikoDesktopPet"
                    self.assertEqual(resolve_save_paths(), SavePaths(
                        directory / "state.sqlite3", directory / "state.json",
                    ))
                    self.assertEqual(default_save_path(), directory / "state.json")
                    self.assertFalse(directory.exists())

    def test_suffix_rules_preserve_designated_source_and_destination(self) -> None:
        for name, database, legacy in (
            ("pet.json", "pet.sqlite3", "pet.json"),
            ("pet.JSON", "pet.sqlite3", "pet.JSON"),
            ("pet.sqlite3", "pet.sqlite3", "pet.json"),
            ("pet.sqlite", "pet.sqlite", "pet.json"),
            ("pet.DB", "pet.DB", "pet.json"),
            ("pet", "pet.sqlite3", "pet"),
            ("pet.save", "pet.save.sqlite3", "pet.save"),
        ):
            with self.subTest(name=name), patch.dict(
                os.environ, {"AIKO_SAVE_PATH": f"test-saves/{name}"},
            ):
                self.assertEqual(resolve_save_paths(), SavePaths(
                    ROOT / "test-saves" / database, ROOT / "test-saves" / legacy,
                ))

    def test_quotes_expansion_and_os_environment_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            env = Path(folder) / "fixture.env"
            env.write_text("AIKO_SAVE_PATH=ignored.json", encoding="utf-8")
            for quote in ("'", '"'):
                with self.subTest(quote=quote), patch.dict(os.environ, {
                    "AIKO_SAVE_PATH": f" {quote}$AIKO_PATH_FIXTURE/my save.json{quote}",
                    "AIKO_PATH_FIXTURE": folder,
                }):
                    load_env_file(env)
                    self.assertEqual(resolve_save_paths(), SavePaths(
                        Path(folder) / "my save.sqlite3", Path(folder) / "my save.json",
                    ))
            with patch.dict(os.environ, {"AIKO_SAVE_PATH": "~/aiko-fixture.json"}):
                self.assertEqual(resolve_save_paths().legacy_json,
                                 Path.home() / "aiko-fixture.json")

    def test_explicit_database_wins_without_reading_or_falling_back(self) -> None:
        with tempfile.TemporaryDirectory() as folder, patch.dict(
            os.environ, {"AIKO_SAVE_PATH": "ignored.json"},
        ):
            database = Path(folder) / "missing" / "save.sqlite3"
            self.assertEqual(resolve_save_paths(database), SavePaths(
                database, database.with_suffix(".json"),
            ))
            self.assertFalse(database.parent.exists())

    def test_existing_json_public_import_keeps_the_same_owner(self) -> None:
        self.assertIs(public_json_path, default_save_path)


if __name__ == "__main__":
    unittest.main()
