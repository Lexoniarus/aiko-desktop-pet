"""The local routine reads its exact original schedule from JSON."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from aiko_pet.pet.routine import (
    SUNDAY_SLOTS,
    WEEKDAY_SLOTS,
    WEEKEND_SLOTS,
)
from aiko_pet.pet.routine_catalog import parse_routine_catalog


class RoutineCatalogTests(unittest.TestCase):
    def test_weekday_and_weekend_slots_are_loaded_from_json(self) -> None:
        path = (Path(__file__).resolve().parents[1]
                / "aiko_pet" / "data" / "routine.de.json")
        catalog = parse_routine_catalog(json.loads(path.read_text("utf-8")))
        self.assertEqual(catalog.weekdays, WEEKDAY_SLOTS)
        self.assertEqual(catalog.saturday, WEEKEND_SLOTS)
        self.assertEqual(catalog.sunday, SUNDAY_SLOTS)
        self.assertEqual(WEEKDAY_SLOTS[1], (
            450, "breakfast", "Frühstückszeit", "breakfast",
        ))
        self.assertEqual(SUNDAY_SLOTS[-1], (1410, "night", "Nachtruhe", None))

    def test_invalid_day_and_unsupported_schema_fail_early(self) -> None:
        slot = {"minute": 0, "period": "night",
                "label": "Nachtruhe", "meal": None}
        base = {"version": 1, "weekdays": [slot],
                "saturday": [slot], "sunday": [slot]}
        self.assertEqual(parse_routine_catalog(base).weekdays[0][0], 0)
        for bad in (
            {**base, "version": 2},
            {**base, "sunday": []},
            {**base, "weekdays": [{**slot, "minute": 30}]},
            {**base, "weekdays": [slot, slot]},
            {**base, "saturday": [slot, {
                "minute": 800, "period": "lunch",
                "label": "Mittag", "meal": "dinner",
            }]},
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    parse_routine_catalog(bad)
