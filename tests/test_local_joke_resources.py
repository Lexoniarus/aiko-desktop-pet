"""Resource integrity failures are classified before constructing a desktop."""

import json
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest.mock import Mock, patch

from aiko_pet.desktop.startup import run_desktop
from aiko_pet.infrastructure.local_jokes import (
    REVIEW_PATH,
    LocalJokeCatalogError,
    load_local_jokes,
)
from aiko_pet.infrastructure.runtime_dependencies import (
    RuntimeDependencyError,
    check_runtime_dependencies,
)


class LocalJokeResourceTests(unittest.TestCase):
    def test_missing_malformed_empty_or_duplicate_key_review_is_classified(self):
        review = REVIEW_PATH.read_text(encoding="utf-8")
        empty = json.loads(review)
        empty["entries"] = []
        duplicate = review.replace('"version": 1,', '"version": 1, "version": 1,', 1)
        for body in (None, "{", json.dumps(empty), duplicate):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "review.json"
                if body is not None:
                    path.write_text(body, encoding="utf-8")
                with self.assertRaises(LocalJokeCatalogError) as raised:
                    load_local_jokes(path)
                self.assertEqual(raised.exception.kind, "review")

    def test_changed_review_hash_is_classified_as_content_mismatch(self):
        raw = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        raw["entries"][0]["fingerprint"] = "0" * 64
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "review.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(LocalJokeCatalogError) as raised:
                load_local_jokes(path)
        self.assertEqual(raised.exception.kind, "content")

    def test_changed_library_at_same_version_stops_before_application_creation(self):
        jokes = list(import_module("pyjokes").get_jokes(
            language="de", category="neutral",
        ))
        jokes[4] = "Ein geänderter, nicht freigegebener Testtext."
        create = Mock()
        with patch("pyjokes.get_jokes", return_value=jokes), patch(
            "aiko_pet.desktop.startup.messagebox.showerror",
        ) as report, self.assertRaises(SystemExit) as raised:
            run_desktop(create)
        self.assertEqual(raised.exception.code, 1)
        create.assert_not_called()
        report.assert_called_once()
        message = report.call_args.args[1]
        self.assertIn("Freigabeliste", message)
        self.assertIn("frischen Ordner", message)
        self.assertIn("Spielstand wurde nicht geöffnet", message)

    def test_missing_review_reports_project_repair_through_existing_check(self):
        with tempfile.TemporaryDirectory() as folder, patch(
            "aiko_pet.infrastructure.local_jokes.REVIEW_PATH",
            Path(folder) / "missing.json",
        ), self.assertRaises(RuntimeDependencyError) as raised:
            check_runtime_dependencies()
        self.assertIn("Projektdateien", str(raised.exception))

    def test_known_library_errors_are_classified_and_programming_errors_propagate(self):
        language_error = import_module("pyjokes.exc").LanguageNotFoundError
        for failure in (language_error("de"), TypeError("invalid contents")):
            with self.subTest(error=type(failure)), patch(
                "pyjokes.get_jokes", side_effect=failure,
            ), self.assertRaises(LocalJokeCatalogError) as raised:
                load_local_jokes()
            self.assertEqual(raised.exception.kind, "content")
        with patch("pyjokes.get_jokes", side_effect=AssertionError("unexpected")), (
            self.assertRaises(AssertionError)
        ):
            load_local_jokes()
