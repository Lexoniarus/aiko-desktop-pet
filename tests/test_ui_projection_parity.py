"""Parity and ownership tests for semantic snapshots and German UI copy."""

from __future__ import annotations

import random
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.settings import PetSettings
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import encode_pet_state
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.routine import MEAL_NAMES, context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.status_hints import MoodHint
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.view_models.contracts import (
    HoverAnchor,
)
from aiko_pet.ui.view_models.projections import project_hover, project_status
from aiko_pet.ui.view_models.read_models import DesktopPresentation
from aiko_pet.ui.view_models.text_de import (
    describe_workload,
    format_day_label,
    format_feed_label,
    format_mood_hint,
    format_percent,
    format_schedule_line,
    mood_hint_text,
)
from tools.pet_test_support import set_test_pet_values


def at(hour: int, *, day: int = 12) -> float:
    return datetime(2026, 10, day, hour).timestamp()


class StaticMonitor:
    def __init__(self, reading: ComputerSnapshot) -> None:
        self.reading = reading

    def latest(self) -> ComputerSnapshot:
        return self.reading


class UiProjectionParityTests(unittest.TestCase):
    def test_snapshot_copies_mutable_pet_values(self) -> None:
        state = PetState(satiety=19, affection=28, meals_today=["breakfast"])
        snapshot = snapshot_pet(state)
        set_test_pet_values(state, satiety=95)
        set_test_pet_values(state, affection=100)
        set_test_pet_values(state, meals_today=[*state.meals_today, "lunch"])
        self.assertEqual(snapshot.satiety, 19)
        self.assertEqual(snapshot.affection, 28)
        self.assertEqual(snapshot.meals_today, ("breakfast",))
        self.assertEqual(snapshot.needs[0], ("satiety", 19))
        with self.assertRaises(FrozenInstanceError):
            setattr(snapshot, "sleeping", True)

    def test_de_labels_match_semantic_pet_hints(self) -> None:
        states = (
            PetState(),
            PetState(sleeping=True),
            PetState(satiety=10),
            PetState(energy=10),
            PetState(social=10),
            PetState(affection=10),
            PetState(mood=10),
            PetState(satiety=99, mood=99, energy=99,
                     social=99, affection=99),
        )
        for stamp in (at(2), at(8), at(13), at(18), at(23), at(10, day=18)):
            context = context_at(stamp)
            weekdays = (
                "Montag", "Dienstag", "Mittwoch", "Donnerstag",
                "Freitag", "Samstag", "Sonntag",
            )
            self.assertEqual(
                format_day_label(context),
                f"{weekdays[context.local.weekday()]} · "
                f"{context.local:%H:%M} · {context.activity}",
            )
            self.assertEqual(
                format_schedule_line(context),
                f"Danach: {context.next_activity} um {context.next_time}",
            )
            for state in states:
                with self.subTest(stamp=stamp, needs=state.satiety):
                    snapshot = snapshot_pet(state)
                    meal = state.due_meal(context)
                    expected_label = MEAL_NAMES[meal] if meal is not None else "Snack"
                    self.assertEqual(
                        format_feed_label(snapshot, context), expected_label,
                    )
                    self.assertEqual(
                        format_mood_hint(snapshot, context),
                        mood_hint_text(state.mood_hint(context), context),
                    )
                    self.assertEqual(
                        format_mood_hint(snapshot),
                        mood_hint_text(state.mood_hint()),
                    )

    def test_pet_hint_is_typed_and_wording_is_selected_by_ui(self) -> None:
        state = PetState(satiety=10, energy=10)
        self.assertIs(state.mood_hint(), MoodHint.HUNGRY)
        self.assertEqual(
            mood_hint_text(state.mood_hint()),
            "Ein kleiner Snack wäre schön ...",
        )
        set_test_pet_values(state, sleeping=True)
        self.assertIs(state.mood_hint(context_at(at(2))), MoodHint.SLEEP_NIGHT)
        self.assertEqual(
            mood_hint_text(state.mood_hint(context_at(at(2)))),
            "Aiko schläft gerade ... gute Nacht.",
        )

    def test_workload_and_percent_copy_matches_original_thresholds(self) -> None:
        cases = (
            (ComputerSnapshot(), "Ich orientiere mich noch ..."),
            (ComputerSnapshot(cpu=15, measured_at=10),
             "Ich habe gerade etwas Ruhe."),
            (ComputerSnapshot(cpu=45, measured_at=10), "Ich bin beschäftigt."),
            (ComputerSnapshot(cpu=75, measured_at=10),
             "Ich habe ordentlich zu tun."),
            (ComputerSnapshot(cpu=95, gpu=90, measured_at=10),
             "Ich bin gerade voll konzentriert."),
        )
        for reading, expected in cases:
            with self.subTest(cpu=reading.cpu):
                self.assertEqual(describe_workload(reading), expected)
        for value, expected in (
            (None, "–"), (0, "0 %"), (50.4, "50 %"),
            (99.8, "100 %"), (150, "100 %"),
        ):
            with self.subTest(percent=value):
                self.assertEqual(format_percent(value), expected)

    def test_hover_and_status_keep_needs_and_observation_preferences(self) -> None:
        mind = make_aiko_mind(started_at=0.0, rng=random.Random(9))
        states = (
            PetState(),
            PetState(sleeping=True),
            PetState(satiety=8, social=18, affection=22),
        )
        readings = (
            ComputerSnapshot(),
            ComputerSnapshot(cpu=75, gpu=20, ram=70, measured_at=900),
        )
        for stamp in (at(8), at(15), at(23)):
            context = context_at(stamp)
            for state in states:
                for reading in readings:
                    for enabled in (True, False):
                        with self.subTest(stamp=stamp, enabled=enabled):
                            before = encode_pet_state(state)
                            copy = snapshot_pet(state)
                            hover = project_hover(
                                copy, context, reading,
                                observe_computer=enabled,
                            )
                            status = project_status(
                                copy, context, mind.emotion(state, 1000),
                                None, reading, observe_computer=enabled,
                            )
                            for key in (
                                "satiety", "mood", "energy", "social",
                                "affection", "friendship",
                            ):
                                self.assertEqual(
                                    hover.need_value(key), getattr(state, key),
                                )
                                self.assertEqual(
                                    status.need_value(key), getattr(state, key),
                                )
                            expected = "Wecken" if state.sleeping else "Schlafen"
                            self.assertEqual(hover.sleep_label, expected)
                            self.assertEqual(status.sleep_label, expected)
                            if not enabled:
                                self.assertEqual(hover.workload_line, "")
                                self.assertEqual(status.activity_line, "")
                                self.assertEqual(
                                    hover.hardware_line,
                                    "Rechnerbeobachtung deaktiviert",
                                )
                            self.assertEqual(encode_pet_state(state), before)

    def test_desktop_adapter_owns_only_read_projections_and_geometry(self) -> None:
        state = PetState(energy=39)
        settings = PetSettings(
            x=150, y=430, scale=2, toolbar_x=25, toolbar_y=35,
            observe_computer=True,
        )
        mind = make_aiko_mind(started_at=0.0, rng=random.Random(10))
        readings = StaticMonitor(
            ComputerSnapshot(cpu=83, measured_at=100),
        )
        source = DesktopPresentation(
            state, settings, mind, AdaptiveRoutine(), readings,
            context=lambda: context_at(at(15)),
            sprite_size=lambda: (256, 416),
        )
        original = source.hover()
        self.assertIn("CPU 83 %", original.hardware_line)
        self.assertEqual(source.anchor(), HoverAnchor(
            150, 430, 256, 416, 25, 35,
        ))
        self.assertEqual(source.settings_view().value("auto_walk"), True)
        set_test_pet_values(state, energy=70)
        self.assertEqual(original.need_value("energy"), 39)
        self.assertEqual(source.hover().need_value("energy"), 70)
        self.assertEqual(source.status().need_value("energy"), 70)


if __name__ == "__main__":
    unittest.main()
