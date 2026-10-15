"""Aiko's static German wording is validated JSON, not policy source."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiko_pet.pet.content import (
    GERMAN_TEXT,
    load_packaged_text_catalog,
    parse_text_catalog,
)
from aiko_pet.pet.mind.catalog import EMOTIONS
from aiko_pet.pet.status_hints import MoodHint
from aiko_pet.ui.view_models.text_de import (
    format_emotion_label,
    format_sleep_label,
    observation_disabled_text,
)


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

    def test_emotion_and_duplicate_status_copy_have_one_json_owner(self) -> None:
        expected_labels = {
            "asleep": "Schläfrig",
            "irritated": "Gereizt",
            "tired": "Müde",
            "hungry": "Hungrig",
            "withdrawn": "Nachdenklich",
            "warm": "Zugewandt",
            "playful": "Verspielt",
            "calm": "Gelassen",
            "lonely": "Vermisst Gesellschaft",
            "seeking_affection": "Wünscht Zuwendung",
        }
        self.assertEqual(
            {key for key in GERMAN_TEXT.messages if key.startswith("emotion.")},
            {f"emotion.{emotion}" for emotion in EMOTIONS},
        )
        for emotion, expected in expected_labels.items():
            with self.subTest(emotion=emotion):
                self.assertEqual(
                    format_emotion_label(emotion), f"Stimmung: {expected}",
                )
        self.assertEqual(format_sleep_label(True), "Wecken")
        self.assertEqual(format_sleep_label(False), "Schlafen")
        self.assertEqual(
            observation_disabled_text(), "Rechnerbeobachtung deaktiviert",
        )

    def test_game_reactions_are_backed_by_german_json(self) -> None:
        from aiko_pet.ui.windows.rock_paper_scissors_text_de import (
            countdown_line,
            welcome_line,
        )

        messages = GERMAN_TEXT.messages
        for category in ("welcome", "win", "loss", "draw"):
            with self.subTest(category=category):
                self.assertEqual(
                    {f"rps.{category}.{i}" for i in range(3)},
                    {
                        key for key in messages
                        if key.startswith(f"rps.{category}.")
                    },
                )
        for number in (1, 2, 3):
            self.assertEqual(
                countdown_line(number),
                messages[f"rps.countdown.{number}"],
            )
        for games in range(7):
            self.assertEqual(
                welcome_line(games),
                messages[f"rps.welcome.{games % 3}"],
            )
        with self.assertRaises(KeyError):
            countdown_line(4)

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
