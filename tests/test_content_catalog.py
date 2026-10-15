"""Aiko's static German wording is validated JSON, not policy source."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiko_pet.content import (
    GERMAN_TEXT, load_packaged_text_catalog, parse_text_catalog,
)
from aiko_pet.pet.status_hints import MoodHint


class TextCatalogTests(unittest.TestCase):
    def test_packaged_copy_and_templates_are_read_only(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "aiko_pet" / "data" / "texts.de.json"
        )
        decoded = json.loads(path.read_text(encoding="utf-8"))
        loaded = parse_text_catalog(decoded)
        self.assertEqual(dict(loaded.messages), dict(GERMAN_TEXT.messages))
        self.assertEqual(load_packaged_text_catalog(), loaded)
        self.assertEqual(
            GERMAN_TEXT.format("care.feed_repeat", food="Apfel"),
            "Schon wieder Apfel? ...Na gut.",
        )

    def test_all_mood_hint_keys_have_a_german_translation(self) -> None:
        self.assertEqual(
            {f"mood.{hint.value}" for hint in MoodHint},
            {k for k in GERMAN_TEXT.messages if k.startswith("mood.")},
        )

    def test_invalid_templates_and_catalogues_are_rejected(self) -> None:
        for raw in (
            {"version": 2, "locale": "de", "messages": {"care.x": "Hallo"}},
            {"version": 1, "locale": "en", "messages": {"care.x": "Hello"}},
            {"version": 1, "locale": "de", "messages": {}},
            {"version": 1, "locale": "de",
             "messages": {"care.x": "{food.__class__}"}},
            {"version": 1, "locale": "de",
             "messages": {"care.x": "{value:>5}"}},
            {"version": 1, "locale": "de",
             "messages": {"care.x": "{missing"}},
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_text_catalog(raw)
