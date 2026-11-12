"""Regression checks for the public entry point and optional .env handling."""

import os
import runpy
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.application.runtime_resources import PreparedRuntimeResources
from aiko_pet.config import load_env_file

ROOT = Path(__file__).resolve().parents[1]


class LaunchAndEnvironmentTests(unittest.TestCase):
    def test_main_py_starts_the_companion_desktop_checkout(self) -> None:
        desktop = ROOT.with_name("aiko-desktop-pet")
        entry = desktop / "aiko_pet" / "__main__.py"
        gui = desktop / "aiko_pet" / "gui.py"
        interpreter = desktop / ".venv" / "Scripts" / "python.exe"
        starter = desktop / "dist" / "room" / "starter"
        with (
            patch.object(
                Path,
                "is_dir",
                autospec=True,
                side_effect=lambda p: p == starter,
            ),
            patch.object(
                Path,
                "is_file",
                autospec=True,
                side_effect=lambda p: p in (entry, gui, interpreter),
            ),
            patch(
                "aiko_pet.desktop.version_launcher.choose_desktop",
                return_value=True,
            ) as choose,
            patch("subprocess.run", return_value=Mock(returncode=0)) as start,
        ):
            runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
        choose.assert_called_once_with(starter, desktop_error=None)
        start.assert_called_once_with(
            [str(interpreter), "-E", "-m", "aiko_pet"],
            cwd=desktop,
            check=False,
        )

    def test_main_py_leaves_room_selection_to_the_launcher(self) -> None:
        with (
            patch(
                "aiko_pet.desktop.version_launcher.choose_desktop",
                return_value=False,
            ),
            patch("subprocess.run") as start_companion,
            patch("aiko_pet.gui.main") as start_desktop,
        ):
            runpy.run_path(str(ROOT / "main.py"), run_name="__main__")
        start_companion.assert_not_called()
        start_desktop.assert_not_called()

    def test_room_entry_blocks_missing_or_room_companion_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            entry = root / "room" / "main.py"
            entry.parent.mkdir()
            shutil.copyfile(ROOT / "main.py", entry)
            companion = root / "aiko-desktop-pet" / "aiko_pet"
            for room_companion in (False, True):
                with self.subTest(room_companion=room_companion):
                    if room_companion:
                        (companion / "browser").mkdir(parents=True)
                        for name in ("__main__.py", "gui.py", "browser/bootstrap.py"):
                            (companion / name).touch()
                    with (
                        patch(
                            "aiko_pet.desktop.version_launcher.choose_desktop",
                            return_value=True,
                        ) as choose,
                        patch("subprocess.run") as subprocess_start,
                        patch("aiko_pet.gui.main") as native_start,
                    ):
                        runpy.run_path(str(entry), run_name="__main__")
                    self.assertIn(
                        str(companion.parent), choose.call_args.kwargs["desktop_error"]
                    )
                    subprocess_start.assert_not_called()
                    native_start.assert_not_called()

    def test_room_choice_remains_available_when_desktop_is_blocked(self) -> None:
        from aiko_pet.desktop import version_launcher

        with (
            tempfile.TemporaryDirectory() as folder,
            patch.object(version_launcher, "Tk") as tk,
            patch.object(version_launcher, "ttk") as widgets,
            patch.object(version_launcher, "messagebox") as messagebox,
            patch.object(version_launcher, "LocalRoomServer") as server,
        ):
            starter = Path(folder)

            def choose_versions() -> None:
                actions = {
                    call.kwargs["text"]: call.kwargs["command"]
                    for call in widgets.Button.call_args_list
                }
                actions["Desktop-Version"]()
                tk.return_value.destroy.assert_not_called()
                actions["Raum-Version"]()

            tk.return_value.mainloop.side_effect = choose_versions
            self.assertFalse(
                version_launcher.choose_desktop(starter, desktop_error="Fehlt")
            )

        messagebox.showerror.assert_called_once_with(
            "Desktop-Version", "Fehlt", parent=tk.return_value
        )
        server.return_value.open.assert_called_once_with()
        server.return_value.close.assert_called_once_with()

    def test_gui_entrypoint_orders_env_resources_and_desktop(self) -> None:
        from aiko_pet.gui import main

        order = []
        resources = PreparedRuntimeResources(())

        def prepare():
            order.append("resources")
            return resources

        def create(*, local_social_content):
            self.assertIs(local_social_content, resources.local_social_content)
            order.append("pet")
            return Mock(run=lambda: order.append("run"))

        with (
            patch(
                "aiko_pet.gui.load_env_file", side_effect=lambda: order.append("env")
            ),
            patch(
                "aiko_pet.desktop.startup.prepare_runtime_resources",
                side_effect=prepare,
            ),
            patch("aiko_pet.gui.DesktopPet", side_effect=create),
        ):
            main()
        self.assertEqual(order, ["env", "resources", "pet", "run"])

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


if __name__ == "__main__":
    unittest.main()
