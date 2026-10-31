"""Indexed sources preserve one catalogue, validation and seeded selection."""

from __future__ import annotations

import copy
import json
import random
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any

from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook
from aiko_pet.pet.routine import context_at
from aiko_pet.ui.windows.rock_paper_scissors_dialogue import GameDialogue
from tools.dialogue_test_support import dialogue_context, dialogue_source_fixture


class DialogueIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.index = self.root / "index.json"
        first = copy.deepcopy(dialogue_source_fixture()["lines"][0])
        first["id"] = "first"
        second = dict(first, id="second")
        self.write("first.json", self.source([first]))
        self.write("second.json", self.source([second]))
        self.manifest = {
            "index_version": 1,
            "catalogue_version": 3,
            "language": "de",
            "files": ["first.json", "second.json"],
            "line_order": ["second", "first"],
        }
        self.write("index.json", self.manifest)

    @staticmethod
    def source(lines: list[dict[str, Any]]) -> dict[str, Any]:
        return dict(catalogue_version=3, language="de", lines=lines)

    def write(self, name: str, value: Any) -> None:
        (self.root / name).write_text(json.dumps(value), encoding="utf-8")

    def test_order_and_seeded_rotation_match_an_explicit_single_source(self) -> None:
        first = json.loads((self.root / "first.json").read_text("utf-8"))["lines"][0]
        second = dict(first, id="second")
        self.write("single.json", self.source([second, first]))
        indexed = DialogueBook.from_file(self.index, rng=random.Random(19))
        single = DialogueBook.from_file(
            self.root / "single.json", rng=random.Random(19),
        )
        self.assertEqual(tuple(line.id for line in indexed.lines), ("second", "first"))
        self.assertEqual(indexed.lines, single.lines)
        context = dialogue_context(context_at(1800000000))
        for now in range(20):
            self.assertEqual(
                indexed.choose(first["event"], context, now),
                single.choose(first["event"], context, now),
            )
        self.assertEqual(indexed.rng.getstate(), single.rng.getstate())

    def test_only_declared_sources_are_read(self) -> None:
        (self.root / "unlisted.json").write_text("broken JSON", encoding="utf-8")
        self.assertEqual(len(DialogueBook.from_file(self.index).lines), 2)

    def test_index_schema_and_versions_are_strict(self) -> None:
        for update in (
            {"index_version": True}, {"index_version": 1.0}, {"index_version": 2},
            {"catalogue_version": True}, {"catalogue_version": 3.0},
            {"catalogue_version": 4}, {"language": "en"}, {"unknown": []},
            {"files": []}, {"files": "first.json"}, {"files": [1]},
            {"line_order": "first"}, {"line_order": [None]},
        ):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.write("index.json", self.manifest | update)
                DialogueBook.from_file(self.index)

    def test_duplicate_files_and_invalid_order_are_rejected(self) -> None:
        for update in (
            {"files": ["first.json", "first.json"]},
            {"line_order": ["first"]},
            {"line_order": ["first", "second", "third"]},
            {"line_order": ["first", "first"]},
        ):
            with self.subTest(update=update), self.assertRaises(ValueError):
                self.write("index.json", self.manifest | update)
                DialogueBook.from_file(self.index)

    def test_duplicate_ids_and_malformed_source_do_not_silently_override(self) -> None:
        first_source = json.loads((self.root / "first.json").read_text("utf-8"))
        self.write("second.json", first_source)
        with self.assertRaisesRegex(ValueError, "Duplicate dialogue IDs"):
            DialogueBook.from_file(self.index)
        for value in (
            first_source | {"language": "en"},
            first_source | {"catalogue_version": True},
            first_source | {"lines": "wrong"},
            first_source | {"extra": True},
            self.manifest,
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.write("second.json", value)
                DialogueBook.from_file(self.index)

    def test_sources_cannot_escape_recurse_or_disappear(self) -> None:
        for name in (
            "../outside.json", "/outside.json", "C:/outside.json",
            "folder\\outside.json", "./first.json", "folder/../first.json",
            "index.json", "missing.json", "first.txt",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.write("index.json", self.manifest | {"files": [name]})
                DialogueBook.from_file(self.index)

    def test_packaged_sources_load_from_a_separate_source_bundle(self) -> None:
        destination = self.root / "bundle"
        shutil.copytree(CATALOGUE.parent, destination)
        self.assertEqual(
            DialogueBook.from_file(destination / "index.json").lines,
            DialogueBook.from_file().lines,
        )
        self.assertFalse((CATALOGUE.parents[2] / "dialogues.de.json").exists())

    def test_existing_standalone_game_uses_the_same_packaged_loader(self) -> None:
        dialogue = GameDialogue()
        for event in ("game_greeting", "game_aiko_win", "game_player_win", "game_draw"):
            with self.subTest(event=event):
                self.assertTrue(dialogue.choose(event))


if __name__ == "__main__":
    unittest.main()
