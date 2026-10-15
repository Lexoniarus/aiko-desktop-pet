"""Regression checks for the public entry point and optional .env handling."""

import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.config import load_env_file
from aiko_pet.infrastructure.persistence import default_save_path

ROOT = Path(__file__).resolve().parents[1]


class LaunchAndEnvironmentTests(unittest.TestCase):
    def test_main_py_invokes_shared_gui_entrypoint(self) -> None:
        with patch("aiko_pet.gui.main") as start:
            runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
        start.assert_called_once_with()

    def test_gui_entrypoint_loads_env_before_creating_desktop(self) -> None:
        from aiko_pet.gui import main

        order = []
        with (
            patch(
                "aiko_pet.gui.load_env_file", side_effect=lambda: order.append("env")
            ),
            patch("aiko_pet.gui.DesktopPet") as pet,
        ):
            pet.side_effect = lambda: order.append("pet") or Mock(
                run=lambda: order.append("run")
            )
            main()
        self.assertEqual(order, ["env", "pet", "run"])

    def test_env_example_requires_no_secrets(self) -> None:
        content = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.assertIn("AIKO_SAVE_PATH=", content)
        self.assertNotIn("API_KEY=", content)

    def test_env_file_reads_only_supported_keys(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / ".env"
            env_file.write_text(
                "# comment\nAIKO_SAVE_PATH='some folder/state.json'\n"
                "IRRELEVANT_TOKEN=should-not-load\n",
                encoding="utf-8",
            )
            with patch.dict(os.environ, {}, clear=True):
                load_env_file(env_file)
                self.assertEqual(
                    os.environ.get("AIKO_SAVE_PATH"), "some folder/state.json"
                )
                self.assertNotIn("IRRELEVANT_TOKEN", os.environ)

    def test_existing_environment_wins_over_dotenv(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / ".env"
            env_file.write_text("AIKO_SAVE_PATH=ignored.json", encoding="utf-8")
            with patch.dict(os.environ, {"AIKO_SAVE_PATH": "keep.json"}):
                load_env_file(env_file)
                self.assertEqual(os.environ["AIKO_SAVE_PATH"], "keep.json")

    def test_missing_dotenv_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {}, clear=True):
                load_env_file(Path(folder) / "missing.env")
                self.assertNotIn("AIKO_SAVE_PATH", os.environ)

    def test_override_changes_save_file_not_its_parent(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            wanted = Path(folder) / "custom" / "state.json"
            with patch.dict(os.environ, {"AIKO_SAVE_PATH": str(wanted)}):
                self.assertEqual(default_save_path(), wanted)

    def test_blank_override_preserves_platform_default(self) -> None:
        with patch.dict(os.environ, {"AIKO_SAVE_PATH": "  "}):
            self.assertEqual(default_save_path().name, "state.json")
            self.assertEqual(default_save_path().parent.name, "AikoDesktopPet")


if __name__ == "__main__":
    unittest.main()
