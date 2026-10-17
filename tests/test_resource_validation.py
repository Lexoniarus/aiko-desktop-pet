"""Bad authored resources fail before a user opens the affected interface."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.balance import parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.content import parse_text_catalog
from aiko_pet.pet.food import FoodState
from aiko_pet.pet.food_catalog import parse_food_catalog
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.routine_catalog import parse_routine_catalog
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.food_models import food_choices
from aiko_pet.ui.view_models.projections import project_hover

DATA = Path(__file__).resolve().parents[1] / "aiko_pet/data"


class ResourceValidationTests(unittest.TestCase):
    def test_dialogue_weights_use_integer_scale_not_normalized_fractions(self) -> None:
        original = load_json(DATA / "balance.json")
        line = load_json(DATA / "dialogues.de.json")["lines"][0]
        line.pop("weight", None)
        for weight in range(1, 11):
            with self.subTest(weight=weight):
                raw = copy.deepcopy(original)
                raw["dialogue"]["default_weight"] = weight
                balance = parse_balance(raw)
                with patch("aiko_pet.pet.mind.catalog.BALANCE", balance):
                    self.assertEqual(Line.parse(line).weight, weight)
        for weight in (0, 11, True, 1.5):
            with self.subTest(invalid_weight=weight):
                raw = copy.deepcopy(original)
                raw["dialogue"]["default_weight"] = weight
                with self.assertRaises(ValueError):
                    parse_balance(raw)

    def test_normalized_weights_still_reject_values_above_one(self) -> None:
        original = load_json(DATA / "balance.json")
        for section, key in (
            ("mood", "fun_weight"),
            ("mood", "social_weight"),
            ("food_activity", "short_window_weight"),
            ("dialogue", "spontaneous_story_probability"),
        ):
            with self.subTest(section=section, key=key):
                raw = copy.deepcopy(original)
                raw[section][key] = 1.1
                with self.assertRaises(ValueError):
                    parse_balance(raw)

    def test_recent_food_uses_the_nutrition_display_name(self) -> None:
        state = PetState(food=FoodState(recent_food_ids=("apple",)))
        view = project_hover(
            snapshot_pet(state),
            context_at(1_760_000_000),
            ComputerSnapshot(),
            observe_computer=False,
        )
        self.assertIn("Zuletzt: Apfel", view.food_line)
        self.assertNotIn("Apple", view.food_line)

    def test_drink_effect_and_menu_share_the_same_balance_value(self) -> None:
        raw = load_json(DATA / "balance.json")
        raw["care"]["energy_drink_gain"] = 15.0
        balance = parse_balance(raw)
        with patch("aiko_pet.pet.care_actions.BALANCE", balance):
            state = PetState(energy=30)
            state.interact("energy_drink", now=1_760_000_000)
        with patch("aiko_pet.ui.view_models.food_models.BALANCE", balance):
            choices = food_choices(load_item_catalog())
        drink = next(item for item in choices if item.id == "energy_drink")
        self.assertEqual(state.energy, 45)
        self.assertEqual(drink.benefit_label, "+15 Energie")

    def test_duplicate_keys_and_nonfinite_numbers_report_the_resource(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "invalid-resource.json"
            for source in (
                '{"version": 1, "version": 2}',
                '{"nested": [{"id": "one", "id": "two"}]}',
                '{"value": NaN}',
                '{"value": Infinity}',
                '{"value": 1e999}',
            ):
                with self.subTest(source=source):
                    path.write_text(source, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, path.name):
                        load_json(path)

    def test_ui_keys_and_placeholders_match_the_callers_contract(self) -> None:
        original = load_json(DATA / "texts.de.json")
        for operation in ("missing", "unknown", "placeholder", "attribute"):
            raw = copy.deepcopy(original)
            if operation == "missing":
                del raw["messages"]["care.feed_repeat"]
            elif operation == "unknown":
                raw["messages"]["care.feed_repeet"] = "Typo"
            elif operation == "placeholder":
                raw["messages"]["care.feed_repeat"] = "{foood}"
            else:
                raw["messages"]["care.feed_repeat"] = "{food.__class__}"
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                parse_text_catalog(raw)

    def test_unknown_food_and_schedule_fields_are_rejected(self) -> None:
        food = load_json(DATA / "food_catalog.json")
        food["foods"][0]["instant_satiety_pointz"] = 30
        with self.assertRaisesRegex(ValueError, "instant_satiety_pointz"):
            parse_food_catalog(food)
        routine = load_json(DATA / "routine.de.json")
        routine["weekdays"][0]["minut"] = 0
        with self.assertRaisesRegex(ValueError, "minut"):
            parse_routine_catalog(routine)

    def test_dialogue_event_names_and_filter_types_are_checked(self) -> None:
        original = load_json(DATA / "dialogues.de.json")["lines"][0]
        for key, value in (
            ("event", "__misspelled_event__"),
            ("moods", [{}]),
            ("periods", [[]]),
            ("cooldown_seconds", float("nan")),
        ):
            raw = copy.deepcopy(original)
            raw[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                Line.parse(raw)

    def test_boolean_and_float_versions_are_not_schema_versions(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "dialogues.json"
            for version in (True, 1.0):
                raw = load_json(DATA / "dialogues.de.json")
                raw["catalogue_version"] = version
                file.write_text(json.dumps(raw), encoding="utf-8")
                with self.subTest(version=version), self.assertRaises(ValueError):
                    DialogueBook.from_file(file)
            for loader, target, file in (
                (
                    load_character_catalog,
                    "aiko_pet.infrastructure.character_assets.load_json",
                    ASSET_ROOT / "animations.json",
                ),
                (
                    load_item_catalog,
                    "aiko_pet.infrastructure.item_assets.load_json",
                    ASSET_ROOT / "items/items.json",
                ),
            ):
                raw = load_json(file)
                raw["version"] = True
                with patch(target, return_value=raw), self.assertRaises(ValueError):
                    loader()

    def test_balance_rejects_typos_types_ranges_and_invalid_relationships(self) -> None:
        original = load_json(DATA / "balance.json")
        for section, key, value in (
            ("food", "awake_hunger_points_per_hour", True),
            ("food", "awake_hunger_points_per_hour", -1),
            ("food", "internal_simulation_step_minutes", 0),
            ("food", "maximum_recent_foods", 2.5),
            ("mood", "fun_weight", 0.8),
            ("walk", "pause_min_seconds", 181),
            ("fun", "late_unit_reward_fraction", float("inf")),
            ("ambient", "blink_gap_minimum_seconds", 9),
            ("adaptive_learning", "effort_smoothing_seconds", 0),
            ("attention", "cursor_comment_probability", 2),
            ("simulation", "step_seconds", 1000),
            ("object_behavior", "bounce_restitution_fraction", 1),
            ("object_behavior", "bounce_horizontal_damping_fraction", 1),
            ("object_behavior", "bounce_maximum_contacts", 33),
            ("object_behavior", "bounce_minimum_speed", 0),
            ("object_behavior", "presentation_seconds", 0),
            ("object_behavior", "absence_seconds", .1),
            ("object_behavior", "presentation_jitter_widths", 0.4),
            ("object_behavior", "presentation_vertical_widths", 0),
            ("simulation", "maximum_catchup_seconds", 8 * 86400),
        ):
            raw = copy.deepcopy(original)
            raw[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                parse_balance(raw)
        raw = copy.deepcopy(original)
        raw["food"]["awake_hunger_pointz_per_hour"] = 8
        with self.assertRaisesRegex(ValueError, "awake_hunger_pointz"):
            parse_balance(raw)


if __name__ == "__main__":
    unittest.main()
