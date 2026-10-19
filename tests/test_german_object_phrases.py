"""German object speech inflects known names and keeps unknown evidence honest."""

import copy
import tempfile
import unittest
from collections.abc import MutableMapping
from pathlib import Path
from typing import cast

from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.content import (
    GERMAN_OBJECT_GRAMMAR,
    load_packaged_object_grammar,
    parse_object_grammar,
)
from aiko_pet.pet.mind.catalog import DialogueBook, Line, Reaction
from aiko_pet.pet.object_text_contract import (
    OBJECT_TEXT_FIELDS,
    ObjectGrammar,
    ObjectGrammarCatalog,
)
from aiko_pet.ui.view_models.german_object_phrases import object_phrases
from aiko_pet.ui.view_models.object_reactions import format_object_reaction


class GermanObjectPhraseTests(unittest.TestCase):
    def test_all_consumables_have_complete_cases_and_pronouns(self):
        items = load_item_catalog()
        masculine = {
            "apple", "dango", "donut", "cookie", "cupcake", "energy_drink",
        }
        neuter = {"onigiri", "sandwich", "taiyaki", "melonpan", "dorayaki"}
        self.assertEqual(set(items.foods), masculine | neuter)
        for identity, item in items.foods.items():
            with self.subTest(identity=identity):
                forms = object_phrases(identity, item.label)
                noun = "Energy-Drink" if identity == "energy_drink" else item.label
                self.assertEqual(set(forms), OBJECT_TEXT_FIELDS)
                expected = (
                    ("ein", "einen", "einem", "der", "den", "dem",
                     "mein", "meinen", "meinem", "er", "ihn", "ihm")
                    if identity in masculine else
                    ("ein", "ein", "einem", "das", "das", "dem",
                     "mein", "mein", "meinem", "es", "es", "ihm")
                )
                for index, form in enumerate(("indef", "def", "poss", "pron")):
                    for offset, case in enumerate(("nom", "acc", "dat")):
                        word = expected[index * 3 + offset]
                        phrase = word if form == "pron" else f"{word} {noun}"
                        field = f"item_{form}_{case}"
                        self.assertEqual(forms[field], phrase)
                        capital = "I" + field[1:]
                        self.assertEqual(forms[capital], phrase[0].upper() + phrase[1:])
                self.assertEqual(forms["item"], noun)
        # A spoken override does not rename the menu's canonical item.
        self.assertEqual(items.foods["energy_drink"].label, "Energy Drink")

    def test_feminine_forms_and_unknown_possession(self):
        grammar = ObjectGrammarCatalog({"pear": ObjectGrammar("feminine")})
        forms = object_phrases("pear", "Birne", grammar=grammar)
        self.assertEqual(forms["item_indef_dat"], "einer Birne")
        self.assertEqual(forms["item_def_acc"], "die Birne")
        self.assertEqual(forms["item_poss_nom"], "meine Birne")
        self.assertEqual(forms["item_poss_dat"], "meiner Birne")
        self.assertEqual(forms["item_pron_acc"], "sie")
        self.assertEqual(forms["item_pron_dat"], "ihr")
        for identity, label in ((None, "Onigiri"), ("unlearned", "Onigiri"),
                                ("onigiri", None)):
            unknown = object_phrases(identity, label)
            self.assertEqual(unknown["item_indef_nom"], "ein Gegenstand")
            self.assertEqual(unknown["item_poss_nom"], "der Gegenstand")
            self.assertEqual(unknown["item_poss_acc"], "den Gegenstand")
            self.assertEqual(unknown["item_poss_dat"], "dem Gegenstand")
            self.assertTrue(all("Onigiri" not in value for value in unknown.values()))

    def test_complete_object_sequences_render_without_losing_other_beats(self):
        items = load_item_catalog()
        for line in DialogueBook.from_file().lines:
            if not line.event.startswith("object_"):
                continue
            source = Reaction(line.id, line.beats, line.animation, line.event)
            for identity in (None, *items.foods):
                with self.subTest(line=line.id, identity=identity):
                    result = format_object_reaction(source, identity, items)
                    self.assertNotIn("{", result.text)
                    self.assertEqual(result.event, source.event)
                    self.assertEqual(result.line_id, source.line_id)
                    self.assertEqual(result.animation, source.animation)
                    self.assertEqual(len(result.beats), len(source.beats))
                    for old, new in zip(source.beats, result.beats, strict=True):
                        if old.kind != "text":
                            self.assertEqual(new, old)

    def test_new_identification_and_search_use_different_full_phrases(self):
        lines = {line.id: line for line in DialogueBook.from_file().lines}
        expected = {
            "object-recognized-01": "Ah, ein Onigiri!",
            "voice-object_recognized-0011": "Oh, ein Onigiri! Jetzt erkenne ich es.",
            "object-place-missing-here": "Hä? Wo ist denn mein Onigiri hin?",
            "object-found-nearby": "Ah, da ist mein Onigiri.",
        }
        for key, text in expected.items():
            line = lines[key]
            result = format_object_reaction(
                Reaction(line.id, line.beats, line.animation, line.event),
                "onigiri", load_item_catalog(),
            )
            self.assertEqual(result.text, text)
        for text in ("{item_indef_nom}", "{Item_poss_acc}"):
            with self.assertRaisesRegex(ValueError, "placeholder"):
                Line.parse(dict(
                    id="bad", event="click_notice", animation="idle",
                    beats=[dict(kind="text", content=text)],
                    moods=[], periods=[], weekdays=[],
                ))


class ObjectGrammarResourceTests(unittest.TestCase):
    path = Path(__file__).resolve().parents[1] / "aiko_pet/data/object_grammar.de.json"

    def test_packaged_metadata_has_one_immutable_owner(self):
        loaded = load_packaged_object_grammar()
        self.assertEqual(loaded, GERMAN_OBJECT_GRAMMAR)
        with self.assertRaises(TypeError):
            cast(MutableMapping[str, ObjectGrammar], loaded.entries)["onigiri"] = (
                ObjectGrammar("masculine")
            )

    def test_malformed_metadata_is_rejected_at_load(self):
        original = load_json(self.path)
        invalid = []
        for key, value in (("version", True), ("version", 2), ("locale", "en"),
                           ("extra", True), ("objects", [])):
            raw = copy.deepcopy(original)
            raw[key] = value
            invalid.append(raw)
        for row in ({}, {"gender": "plural"}, {"gender": []},
                    {"gender": "neuter", "name": "Onigiri"}):
            raw = copy.deepcopy(original)
            raw["objects"]["onigiri"] = row
            invalid.append(raw)
        for value in (None, "", " Onigiri", "Onigiri\n", "{item}", "a" * 81):
            raw = copy.deepcopy(original)
            raw["objects"]["onigiri"]["spoken_name"] = value
            invalid.append(raw)
        raw = copy.deepcopy(original)
        del raw["objects"]["onigiri"]
        invalid.append(raw)
        raw = copy.deepcopy(original)
        raw["objects"]["invented"] = {"gender": "neuter"}
        invalid.append(raw)
        for raw in invalid:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_object_grammar(raw)

    def test_duplicate_resource_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad-grammar.json"
            path.write_text('{"version":1,"version":1}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                load_packaged_object_grammar(path)
