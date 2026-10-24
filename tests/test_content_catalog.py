"""Aiko's static German wording is validated JSON, not policy source."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiko_pet.pet.care_result import CareEffect, CareResult
from aiko_pet.pet.content import (
    GERMAN_TEXT,
    load_packaged_text_catalog,
    parse_text_catalog,
)
from aiko_pet.pet.emotions import EmotionalState
from aiko_pet.pet.status_hints import StatusHint
from aiko_pet.ui.view_models.care_text import format_care_response
from aiko_pet.ui.view_models.text_de import (
    format_emotional_state,
    format_sleep_label,
    observation_disabled_text,
)


class TextCatalogTests(unittest.TestCase):
    def test_feeding_fallbacks_use_complete_food_phrases(self) -> None:
        for effect, expected in (
            (
                CareEffect.FOOD_MEAL,
                "Oh, ein Onigiri! Du hast an mein Essen gedacht. Danke!",
            ),
            (
                CareEffect.FOOD_REPEAT,
                "Schon wieder ein Onigiri? Ich hätte beim nächsten Mal gern "
                "etwas Abwechslung.",
            ),
            (CareEffect.FOOD_SNACK, "Ein Onigiri"),
        ):
            result = CareResult("feed", effect, "onigiri", "lunch")
            text = format_care_response(result)
            if effect == CareEffect.FOOD_SNACK:
                self.assertIn("ein Onigiri", text)
            else:
                self.assertEqual(text, expected)

    def test_packaged_copy_and_templates_are_read_only(self) -> None:
        path = (
            Path(__file__).resolve().parents[1] / "aiko_pet" / "data" / "texts.de.json"
        )
        decoded = json.loads(path.read_text(encoding="utf-8"))
        loaded = parse_text_catalog(decoded)
        self.assertEqual(dict(loaded.messages), dict(GERMAN_TEXT.messages))
        self.assertEqual(load_packaged_text_catalog(), loaded)
        self.assertEqual(
            GERMAN_TEXT.format("care.feed_repeat", food="Apfel"),
            "Schon wieder Apfel? Ich hätte beim nächsten Mal gern etwas Abwechslung.",
        )

    def test_emotion_and_duplicate_status_copy_have_one_json_owner(self) -> None:
        expected_labels = {
            EmotionalState.CHEERFUL: "Fröhlich",
            EmotionalState.PROUD: "Stolz",
            EmotionalState.RELIEVED: "Erleichtert",
            EmotionalState.AFFECTIONATE: "Zugewandt",
            EmotionalState.IRRITATED: "Gereizt",
            EmotionalState.CROWDED: "Bedrängt",
            EmotionalState.FRUSTRATED: "Frustriert",
            EmotionalState.DOWNCAST: "Niedergeschlagen",
            EmotionalState.LONELY: "Einsam",
            EmotionalState.AMBIVALENT: "Zwiegespalten",
            EmotionalState.SUBDUED: "Gedrückt",
            EmotionalState.CALM: "Gelassen",
            EmotionalState.SATISFIED: "Zufrieden",
        }
        self.assertEqual(
            {key for key in GERMAN_TEXT.messages if key.startswith("emotion.")},
            {f"emotion.{emotion}" for emotion in EmotionalState},
        )
        for emotion, expected in expected_labels.items():
            with self.subTest(emotion=emotion):
                self.assertEqual(
                    format_emotional_state(emotion),
                    f"Stimmung: {expected}",
                )
        self.assertEqual(format_sleep_label(True), "Wecken")
        self.assertEqual(format_sleep_label(False), "Schlafen")
        self.assertEqual(
            observation_disabled_text(),
            "Rechnerbeobachtung deaktiviert",
        )

    def test_game_reactions_are_backed_by_german_json(self) -> None:
        from aiko_pet.ui.windows.rock_paper_scissors_dialogue import (
            GameDialogue,
            countdown_line,
        )

        messages = GERMAN_TEXT.messages
        from aiko_pet.pet.mind.catalog import DialogueBook

        book = DialogueBook.from_file()
        for event in ("game_greeting", "game_aiko_win", "game_player_win", "game_draw"):
            self.assertGreaterEqual(sum(line.event == event for line in book.lines), 12)
        for number in (1, 2, 3):
            self.assertEqual(
                countdown_line(number), messages[f"rps.countdown.{number}"]
            )
        greetings = {line.text for line in book.lines if line.event == "game_greeting"}
        dialogue = GameDialogue()
        for _ in range(7):
            self.assertIn(dialogue.choose("game_greeting"), greetings)
        with self.assertRaises(KeyError):
            countdown_line(4)

    def test_all_status_hint_keys_have_a_german_translation(self) -> None:
        self.assertEqual(
            {f"status_hint.{hint.value}" for hint in StatusHint},
            {k for k in GERMAN_TEXT.messages if k.startswith("status_hint.")},
        )

    def test_invalid_templates_and_catalogues_are_rejected(self) -> None:
        for raw in (
            {"version": 2, "locale": "de", "messages": {"care.x": "Hallo"}},
            {"version": 1, "locale": "en", "messages": {"care.x": "Hello"}},
            {"version": 1, "locale": "de", "messages": {}},
            {"version": 1, "locale": "de", "messages": {"care.x": "{food.__class__}"}},
            {"version": 1, "locale": "de", "messages": {"care.x": "{value:>5}"}},
            {"version": 1, "locale": "de", "messages": {"care.x": "{missing"}},
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_text_catalog(raw)
