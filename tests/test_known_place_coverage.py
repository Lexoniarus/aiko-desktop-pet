"""Deliberate learned-place checks do not widen unknown-item discovery."""

import unittest

from aiko_pet.pet.mind.object_attention import (
    AttentionMode,
    KnownPlaceCoverage,
    LookSide,
    ObjectAttention,
)


class KnownPlaceCoverageTests(unittest.TestCase):
    def test_distant_places_require_their_side_without_widening_local_notice(self):
        cases: tuple[tuple[LookSide, float], ...] = ((-1, 0), (1, 6000))
        for width in (192, 384):
            for side, target in cases:
                with self.subTest(width=width, side=side):
                    attention = ObjectAttention(
                        "survey", (side, 0), origin=(3000, 100), width=width,
                    )
                    look = KnownPlaceCoverage(side)
                    self.assertTrue(look.contains(
                        target, attention=attention, ground_bounds=(0, 6000),
                    ))
                    self.assertFalse(attention.sees_environment(target, 0))
                    self.assertFalse(look.contains(
                        6000 - target, attention=attention, ground_bounds=(0, 6000),
                    ))

    def test_requested_coverage_cannot_replace_actual_horizontal_survey_gaze(self):
        look = KnownPlaceCoverage(-1)
        cases: tuple[tuple[AttentionMode, tuple[float, float] | None], ...] = (
            ("object", (-1, 0)), ("unavailable", None),
            ("cursor", (-1, 0)), ("moving", (-1, 0)),
            ("survey", (1, 0)), ("survey", (-1, 1)), ("survey", None),
        )
        for mode, direction in cases:
            with self.subTest(mode=mode, direction=direction):
                self.assertFalse(look.contains(
                    0, attention=ObjectAttention(mode, direction, origin=(3000, 0)),
                    ground_bounds=(0, 6000),
                ))

    def test_world_bounds_and_a_place_at_the_eye_origin(self):
        for side in (-1, 1):
            attention = ObjectAttention("survey", (side, 0), origin=(100, 60))
            look = KnownPlaceCoverage(side)
            self.assertTrue(look.contains(
                100, attention=attention, ground_bounds=(0, 200),
            ))
            for x in (-1, 201):
                self.assertFalse(look.contains(
                    x, attention=attention, ground_bounds=(0, 200),
                ))
