"""Public checkout contracts for media, docs, config and repository safety."""

from __future__ import annotations

import json
import re
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL_MARKDOWN = (
    "README.md", "CONTRIBUTING.md", "ASSETS.md",
    "docs/ARCHITECTURE.md", "docs/MEDIA_GALLERY.md",
    "docs/GITHUB_WORKFLOW.md", "docs/REFACTOR_ACCEPTANCE.md",
)
LOCAL_LINK = re.compile(r"\]\(([^)]+)\)")


def local_links(source: Path) -> set[Path]:
    """Resolve local Markdown targets without fetching anything remotely."""
    text = source.read_text(encoding="utf-8")
    result: set[Path] = set()
    for raw_target in LOCAL_LINK.findall(text):
        target = raw_target.partition("#")[0]
        if (
            not target
            or "://" in target
            or target.startswith(("mailto:", "#"))
        ):
            continue
        result.add((source.parent / target).resolve())
    return result


class PublicRepositoryTests(unittest.TestCase):
    def test_public_docs_have_no_broken_local_links(self) -> None:
        for relative in LOCAL_MARKDOWN:
            document = ROOT / relative
            with self.subTest(document=relative):
                self.assertTrue(document.is_file())
                for path in sorted(local_links(document)):
                    self.assertTrue(
                        path.is_file(),
                        f"{relative} has missing file: {path}",
                    )

    def test_readme_uses_a_real_close_framed_capture_and_animation(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("vorschau/Aiko_v0_13_Dialog_Mitte.png", readme)
        self.assertIn("vorschau/Aiko_v0_13_Reaktionsablauf.gif", readme)
        self.assertIn("docs/MEDIA_GALLERY.md", readme)
        self.assertIn("docs/ARCHITECTURE.md", readme)
        self.assertIn("CONTRIBUTING.md", readme)

    def test_gallery_accounts_for_every_checked_in_preview(self) -> None:
        gallery = (
            ROOT / "docs/MEDIA_GALLERY.md"
        ).read_text(encoding="utf-8")
        for asset in sorted((ROOT / "vorschau").iterdir()):
            if not asset.is_file() or asset.suffix.lower() not in (
                ".png", ".gif",
            ):
                continue
            with self.subTest(asset=asset.name):
                self.assertIn(asset.name, gallery)
                sample = asset.read_bytes()
                if asset.suffix.lower() == ".png":
                    self.assertTrue(sample.startswith(b"\x89PNG\r\n\x1a\n"))
                    width, height = struct.unpack(">II", sample[16:24])
                    self.assertGreater(width, 0)
                    self.assertGreater(height, 0)
                else:
                    self.assertIn(sample[:6], (b"GIF87a", b"GIF89a"))

    def test_provenance_matches_actual_sprite_frames(self) -> None:
        manifest = json.loads(
            (ROOT / "aiko_pet/assets/provenance.json").read_text(
                encoding="utf-8",
            ),
        )
        frames = ROOT / "aiko_pet/assets/frames"
        for action, count in manifest["frame_counts"].items():
            with self.subTest(action=action):
                self.assertEqual(len(tuple((frames / action).glob("*.png"))), count)
        self.assertEqual(sum(manifest["frame_counts"].values()), 73)
        self.assertEqual(
            len(tuple((ROOT / "aiko_pet/assets/emotes").glob("*.png"))), 15,
        )

    def test_example_environment_is_optional_and_does_not_invent_keys(
        self,
    ) -> None:
        example = (
            ROOT / ".env.example"
        ).read_text(encoding="utf-8")
        keys = {
            line.split("=", 1)[0].strip()
            for line in example.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
            and "=" in line
        }
        self.assertEqual(keys, {"AIKO_SAVE_PATH"})
        self.assertIn("AIKO_SAVE_PATH=", example)
        self.assertNotIn("API_KEY=", example)

    def test_ignored_private_data_and_removed_publisher(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in (
            ".env", ".env.*", "!.env.example", "state.json", "*.sqlite",
            ".mypy_cache/", ".ruff_cache/", ".pyright/", "htmlcov/",
            "*.ttf", "*.otf", "*.exe", "*.log",
        ):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, ignore)
        self.assertFalse((ROOT / "publish_to_github.ps1").exists())

    def test_developer_documentation_and_ci_are_present(self) -> None:
        for path in (
            "docs/ARCHITECTURE.md", "CONTRIBUTING.md",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/PULL_REQUEST_TEMPLATE.md",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())
        for workflow in (
            ".github/workflows/tests.yml",
            ".github/workflows/full_static_audit.yml",
        ):
            source = (ROOT / workflow).read_text(encoding="utf-8")
            self.assertIn("pyright==1.1.414", source)

    def test_refactor_reports_are_marked_historical(self) -> None:
        for relative in (
            "docs/REFACTOR_ARCHITECTURE.md",
            "docs/ARCHITECTURE_AUDIT_20261013.md",
            "docs/REFACTOR_ACCEPTANCE.md",
        ):
            with self.subTest(path=relative):
                preface = (ROOT / relative).read_text(
                    encoding="utf-8",
                )[:550].lower()
                self.assertIn("historical", preface)
                self.assertIn("architecture.md", preface)


if __name__ == "__main__":
    unittest.main()
