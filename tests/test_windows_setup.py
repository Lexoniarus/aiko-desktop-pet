"""Exercise Windows source setup in a disposable copy, without OS installs."""

from __future__ import annotations

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "win32", "Windows setup integration")
@unittest.skipIf(
    os.environ.get("AIKO_TEST_NO_NATIVE_TK") == "1",
    "Installer probes create native Tk in child processes",
)
class WindowsSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="Aiko setup & space ")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        (self.folder / "tools").mkdir()
        shutil.copy2(
            ROOT / "tools/install_windows.ps1",
            self.folder / "tools/install_windows.ps1",
        )
        for filename in (
            "requirements.txt",
            "Aiko_installieren.bat",
            "Aiko_Pet.pyw",
            "Aiko_starten.bat",
            "Aiko_starten_debug.bat",
        ):
            shutil.copy2(ROOT / filename, self.folder / filename)
        # Keep failure cases small; the successful setup needs the real package.
        (self.folder / "aiko_pet").mkdir()
        (self.folder / "aiko_pet/__main__.py").touch()
        self.environment = dict(os.environ)
        self.save = self.folder / "preserved-state.json"
        self.save.write_text('{"existing": "progress"}', encoding="utf-8")
        self.environment["AIKO_SAVE_PATH"] = str(self.save)

    def prepare_offline_dependencies(self) -> None:
        # Package installed dependencies for offline setup checks, preserving
        # native Pillow wheel tags instead of claiming a pure-Python wheel.
        wheels = self.folder / "wheels"
        wheels.mkdir()
        for name in ("astronomy-engine", "pyjokes", "Pillow"):
            package = importlib.metadata.distribution(name)
            metadata = package.read_text("WHEEL") or ""
            tag = next(
                line.removeprefix("Tag: ").strip()
                for line in metadata.splitlines()
                if line.startswith("Tag: ")
            )
            wheel_name = f"{name.lower().replace('-', '_')}-{package.version}-{tag}.whl"
            with zipfile.ZipFile(wheels / wheel_name, "w") as archive:
                for member in package.files or ():
                    if ".." not in member.parts and "__pycache__" not in member.parts:
                        archive.write(
                            str(package.locate_file(member)),
                            member.as_posix(),
                        )
        self.environment["PIP_FIND_LINKS"] = wheels.as_uri()
        self.environment["PIP_NO_INDEX"] = "1"
        self.environment["PIP_CONFIG_FILE"] = os.devnull

    def run_setup(
        self,
        python: str = sys.executable,
    ) -> subprocess.CompletedProcess[str]:
        return self.run_powershell([
            "-File", str(self.folder / "tools/install_windows.ps1"),
            "-PythonExecutable", python, "-NoPythonInstall",
            "-ShortcutDirectory", str(self.folder / "shortcuts"),
        ])

    def run_powershell(self, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        # Hosted Windows runners occasionally need over 90 seconds for a cold
        # PowerShell/venv startup. Preserve the bounded check and expose the last
        # installer output if it really stalls; do not retry a failed installation.
        try:
            return subprocess.run(
                ["powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy",
                 "Bypass", *arguments],
                cwd=self.folder.parent, env=self.environment,
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired as error:
            self.fail(f"Setup exceeded 180 seconds. "
                      f"stdout={error.stdout!r}; stderr={error.stderr!r}")

    def test_install_repeat_and_batch_entry_preserve_runtime_and_save(self) -> None:
        shutil.copytree(
            ROOT / "aiko_pet",
            self.folder / "aiko_pet",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        self.prepare_offline_dependencies()
        for _ in range(2):
            setup = self.run_setup()
            self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
            self.assertEqual(
                self.save.read_text(encoding="utf-8"),
                '{"existing": "progress"}',
            )
        python = self.folder / ".venv/Scripts/python.exe"
        probe = subprocess.run(
            [
                str(python),
                "-c",
                ("import json,sys; print(json.dumps([sys.prefix, sys.base_prefix]))"),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        prefix, base = json.loads(probe.stdout)
        self.assertTrue(Path(prefix).samefile(self.folder / ".venv"))
        self.assertFalse(Path(prefix).samefile(base))
        shortcut = self.folder / "shortcuts/Aiko Desktop Pet.lnk"
        self.assertTrue(shortcut.is_file())
        shortcut_environment = dict(
            self.environment,
            AIKO_TEST_SHORTCUT=str(shortcut),
        )
        shortcut_info = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "$shell = New-Object -ComObject WScript.Shell; "
                "$link = $shell.CreateShortcut($env:AIKO_TEST_SHORTCUT); "
                "@{target=$link.TargetPath;arguments=$link.Arguments;"
                "workingDirectory=$link.WorkingDirectory} | ConvertTo-Json",
            ],
            env=shortcut_environment,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        link = json.loads(shortcut_info.stdout)
        # COM can expand 8.3 aliases in TEMP or the user directory. Compare
        # filesystem identity while still requiring exactly one quoted script.
        self.assertTrue(Path(link["target"]).samefile(python.with_name("pythonw.exe")))
        self.assertRegex(link["arguments"], r'\A"[^"]+"\Z')
        self.assertTrue(
            Path(link["arguments"][1:-1]).samefile(self.folder / "Aiko_Pet.pyw"),
        )
        self.assertTrue(Path(link["workingDirectory"]).samefile(self.folder))
        batch_setup = self.run_batch(
            "Aiko_installieren.bat",
            "-NoPythonInstall",
            "-NoShortcuts",
        )
        self.assertEqual(
            batch_setup.returncode,
            0,
            batch_setup.stdout + batch_setup.stderr,
        )
        self.assertEqual(
            self.save.read_text(encoding="utf-8"),
            '{"existing": "progress"}',
        )

    def test_launchers_select_python_and_propagate_debug_exit(self) -> None:
        venv.EnvBuilder().create(self.folder / ".venv")
        python = self.folder / ".venv/Scripts/python.exe"
        # Exercise the batch files without launching a pet or touching a save.
        marker = self.folder / "launched.json"
        entry = (
            "import json, sys\nfrom pathlib import Path\n"
            f"Path({str(marker)!r}).write_text(json.dumps(sys.executable))\n"
        )
        (self.folder / "aiko_pet/__main__.py").write_text(
            entry + "raise SystemExit(7)\n",
            encoding="utf-8",
        )
        debug = self.run_batch("Aiko_starten_debug.bat")
        self.assertEqual(debug.returncode, 7, debug.stdout + debug.stderr)
        self.assertTrue(Path(json.loads(marker.read_text())).samefile(python))
        marker.unlink()
        (self.folder / "Aiko_Pet.pyw").write_text(entry, encoding="utf-8")
        normal = self.run_batch("Aiko_starten.bat")
        self.assertEqual(normal.returncode, 0, normal.stdout + normal.stderr)
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue(marker.exists(), "Windowless launcher did not run")
        self.assertTrue(
            Path(json.loads(marker.read_text())).samefile(
                python.with_name("pythonw.exe")
            ),
        )

    def test_bad_joke_review_stops_setup_before_shortcuts_or_save_access(self) -> None:
        shutil.copytree(
            ROOT / "aiko_pet",
            self.folder / "aiko_pet",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        self.prepare_offline_dependencies()
        review = self.folder / "aiko_pet/data/pyjokes.de.review.json"
        before = self.save.read_bytes()
        for body in (None, "{"):
            with self.subTest(body=body):
                if body is None:
                    review.unlink()
                else:
                    review.write_text(body, encoding="utf-8")
                result = self.run_setup()
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("Freigabeliste", result.stdout + result.stderr)
                self.assertEqual(self.save.read_bytes(), before)
                self.assertFalse(self.save.with_suffix(".sqlite3").exists())
                shortcut = self.folder / "shortcuts/Aiko Desktop Pet.lnk"
                self.assertFalse(shortcut.exists())

    def run_batch(
        self,
        filename: str,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["cmd.exe", "/d", "/c", filename, *arguments],
            cwd=self.folder,
            env=self.environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_invalid_explicit_python_fails_without_downloading(self) -> None:
        setup = self.run_setup(str(self.folder / "missing-python.exe"))
        self.assertNotEqual(setup.returncode, 0)
        self.assertIn("angegebene Python", setup.stdout)
        self.assertFalse((self.folder / ".venv").exists())

    def test_existing_broken_environment_is_preserved(self) -> None:
        shutil.copytree(
            ROOT / "aiko_pet",
            self.folder / "aiko_pet",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        self.prepare_offline_dependencies()
        environment = self.folder / ".venv"
        environment.mkdir()
        marker = environment / "keep.txt"
        marker.write_text("preserve", encoding="utf-8")
        setup = self.run_setup()
        self.assertEqual(setup.returncode, 0, setup.stdout + setup.stderr)
        backups = list(self.folder.glob(".venv-backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(
            (backups[0] / "keep.txt").read_text(encoding="utf-8"),
            "preserve",
        )
        self.assertTrue((environment / "Scripts/python.exe").is_file())

    def test_incomplete_source_fails_before_environment_creation(self) -> None:
        (self.folder / "requirements.txt").unlink()
        setup = self.run_setup()
        self.assertNotEqual(setup.returncode, 0)
        self.assertIn("gesamten Aiko-Quellordner", setup.stdout)
        self.assertFalse((self.folder / ".venv").exists())

    def run_harness(
        self, source: str, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        harness = self.folder / "setup-test.ps1"
        harness.write_text(source, encoding="utf-8")
        return self.run_powershell(["-File", str(harness), *arguments])

    def download_scenario(
        self,
        scenario: str,
        *,
        installs: int,
        error: str | None = None,
    ) -> None:
        if scenario == "success":
            shutil.copytree(
                ROOT / "aiko_pet",
                self.folder / "aiko_pet",
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
            self.prepare_offline_dependencies()
        source = (ROOT / "tests/fixtures/windows_download.ps1").read_text("utf-8")
        result = self.run_harness(source, sys.executable, scenario)
        output = result.stdout + result.stderr
        if error is None:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
            self.assertIn(error, output)
        self.assertEqual(
            (self.folder / ".venv/Scripts/python.exe").is_file(),
            scenario == "success",
        )
        records = sorted(self.folder.glob("install-*.json"))
        self.assertEqual(len(records), installs)
        if records:
            arguments = json.loads(records[0].read_text())
            for flag in (
                "/quiet",
                "/norestart",
                "InstallAllUsers=0",
                "Include_tcltk=1",
                "Include_pip=1",
            ):
                self.assertIn(flag, arguments)
            if installs == 2:
                self.assertIn("/repair", json.loads(records[1].read_text()))
        url = self.folder / "url.txt"
        if scenario == "no-install":
            self.assertFalse(url.exists())
        else:
            self.assertEqual(
                url.read_text().strip(),
                "https://www.python.org/ftp/python/3.13.16/python-3.13.16-amd64.exe",
            )

    def test_disabled_install_never_downloads(self) -> None:
        self.download_scenario("no-install", installs=0, error="Kein Python")

    def test_offline_download_never_starts_installer(self) -> None:
        self.download_scenario("offline", installs=0, error="Netzwerk nicht erreichbar")

    def test_bad_checksum_never_starts_installer(self) -> None:
        self.download_scenario("bad-hash", installs=0, error="Pruefsumme")

    def test_installer_failure_preserves_exit_code(self) -> None:
        self.download_scenario("failed", installs=1, error="Code 42")

    def test_unusable_runtime_is_rejected_after_repair(self) -> None:
        self.download_scenario("unusable", installs=2, error="nicht startbar")

    def test_runtime_discovery_retries_after_repair(self) -> None:
        self.download_scenario("repair", installs=2)

    def test_reboot_code_is_accepted(self) -> None:
        self.download_scenario("reboot", installs=1)

    def test_automatic_install_connects_download_to_application_setup(self) -> None:
        self.download_scenario("success", installs=1)

    def test_importable_but_broken_tk_is_rejected(self) -> None:
        # Import succeeds, but creating a Tk window fails: a real runtime defect.
        (self.folder / "tkinter.py").write_text(
            "def Tk():\n    raise RuntimeError('broken Tcl/Tk')\n",
            encoding="utf-8",
        )
        result = self.run_harness(
            r"""param([string]$Python)
. "$PSScriptRoot\tools\install_windows.ps1"
Set-Location -LiteralPath $PSScriptRoot
$candidate = Get-CompatiblePython $Python
if ($candidate) { throw 'Accepted broken Tcl/Tk' }
""",
            sys.executable,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_download_architectures_and_unsupported_windows(self) -> None:
        result = self.run_harness(r"""
. "$PSScriptRoot\tools\install_windows.ps1"
@('AMD64', 'x86', 'ARM64') | ForEach-Object { Get-PythonDownload $_ } | ConvertTo-Json
""")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        downloads = json.loads(result.stdout)
        for item, suffix in zip(downloads, ("-amd64", "", "-arm64"), strict=True):
            self.assertTrue(item["Url"].endswith(f"3.13.16{suffix}.exe"))
            self.assertRegex(item["Sha256"], r"^[0-9a-f]{64}$")
        result = self.run_harness(r"""
. "$PSScriptRoot\tools\install_windows.ps1" -NoShortcuts
function Get-ItemProperty { return [pscustomobject]@{ CurrentBuildNumber = '7601' } }
try { Invoke-AikoSetup; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }
""")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Windows 10 oder neuer", result.stdout)
        self.assertFalse((self.folder / ".venv").exists())


if __name__ == "__main__":
    unittest.main()
