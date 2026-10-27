"""Visible warning receipts are required before a new pressure episode."""

import unittest
from dataclasses import replace

from aiko_pet.pet.interaction_events import CursorWarningReceipt
from aiko_pet.pet.mind.catalog import DialogueBook, Line
from aiko_pet.pet.mind.cursor_attention import CursorPerception
from aiko_pet.pet.mind.cursor_behaviour import (
    CursorBehaviourContext,
    CursorBehaviourPolicy,
)


class CursorWarningTests(unittest.TestCase):
    def setUp(self):
        self.policy = CursorBehaviourPolicy(session_id="warning")
        self.context = CursorBehaviourContext(1, 80, 50)

    def sample(self, now, **fields):
        perception = CursorPerception(
            sampled_at=now, pointer=(400, 100), distance=.5, speed=4,
            closing_speed=2, side=1, valid=True,
        )
        return self.policy.evaluate(replace(perception, **fields), self.context, now)

    def receipt(self, first, at: float = 10, shown=True):
        assert first.warning is not None
        self.policy.note_warning(CursorWarningReceipt(
            first.warning.warning_id, at, shown,
        ))

    def test_only_new_approach_after_display_can_qualify(self):
        first = self.sample(10)
        self.assertIsNone(first.experience)
        self.assertFalse(first.moving)
        self.receipt(first)
        self.assertIsNone(self.sample(10).experience)
        self.assertIsNone(self.sample(10.1).experience)
        self.sample(10.2, closing_speed=-2)
        fear = self.sample(10.3)
        assert fear.experience is not None
        self.assertEqual(fear.experience.feeling, "fear")
        self.assertTrue(fear.moving)
        self.assertEqual(fear.attention, self.policy.attention)
        self.assertEqual(fear.stage, self.policy.stage)
        self.assertIsNone(self.sample(10.4).experience)

    def test_speed_threshold_flutter_during_same_approach_is_not_new_pressure(self):
        first = self.sample(10)
        self.receipt(first)
        self.sample(10.1, speed=1.4, closing_speed=1)
        self.assertIsNone(self.sample(10.2).experience)
        self.sample(10.3, closing_speed=-1)
        self.assertIsNotNone(self.sample(10.4).experience)

    def test_dropped_late_wrong_and_reset_receipts_cannot_arm_fear(self):
        for variant in ("dropped", "late", "wrong", "reset"):
            with self.subTest(variant=variant):
                self.policy.reset()
                first = self.sample(10)
                assert first.warning is not None
                warning_id = first.warning.warning_id
                if variant == "reset":
                    self.policy.claim_access(10.1)
                receipt = CursorWarningReceipt(
                    "wrong" if variant == "wrong" else warning_id,
                    10.6 if variant == "late" else 10,
                    variant != "dropped",
                )
                self.policy.note_warning(receipt)
                self.sample(10.7, closing_speed=-2)
                self.assertIsNone(self.sample(10.8).experience)

    def test_three_second_window_and_ten_second_repeat_limit(self):
        first = self.sample(10)
        self.receipt(first)
        for n in range(1, 32):
            self.sample(10 + n / 10, closing_speed=-2)
        late = self.sample(13.2)
        self.assertIsNone(late.experience)
        self.assertIsNone(late.warning)
        self.sample(19.9, closing_speed=-2)
        self.assertIsNotNone(self.sample(20).warning)

    def test_duplicate_receipt_does_not_extend_window(self):
        first = self.sample(10)
        self.receipt(first)
        for n in range(1, 30):
            self.sample(10 + n / 10, closing_speed=-2)
        self.receipt(first, at=12.9)
        self.assertIsNone(self.sample(13.1).experience)

    def test_safe_fast_motion_and_stationary_filter_tail_never_warn(self):
        for fields in (dict(distance=4), dict(closing_speed=-2),
                       dict(closing_speed=.5), dict(stationary_seconds=.4)):
            self.policy.reset()
            self.assertIsNone(self.sample(10, **fields).warning)

    def test_canonical_warning_is_available_at_every_friendship_stage(self):
        from aiko_pet.pet.mind import PetMind
        from aiko_pet.pet.routine import context_at
        from aiko_pet.pet.state import PetState

        mind = PetMind(DialogueBook.from_file())
        for friendship in (0, 30, 60, 100):
            reaction = mind.select_reaction(
                "cursor_warning_near_fast", PetState(friendship=friendship),
                context_at(1800000000), 10,
            )
            assert reaction is not None
            self.assertEqual(len(reaction.beats), 1)
            self.assertEqual(reaction.beats[0].kind, "text")
            self.assertIn("zu nah", reaction.text)

    def test_warning_catalogue_rejects_multiple_cues(self):
        raw = dict(
            id="warning", event="cursor_warning_near_fast", animation="idle",
            periods=[], weekdays=[], beats=[dict(kind="text", content="Langsam!")],
        )
        self.assertEqual(Line.parse(raw).text, "Langsam!")
        for extra in (dict(kind="text", content="Noch einmal"),
                      dict(kind="emote", content="drops")):
            with self.assertRaises(ValueError):
                Line.parse(dict(raw, beats=[*raw["beats"], extra]))
