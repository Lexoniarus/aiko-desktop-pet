"""Headless parity tests for typed mouse-click event decisions."""

from __future__ import annotations

import unittest
from typing import cast
from datetime import datetime

from aiko_pet.personality.adaptive_models import Behaviour
from aiko_pet.personality.click_policy import (
    ClickButton,
    ClickDecision,
    choose_click_reaction,
)
from aiko_pet.pet.state import PetState
from aiko_pet.pet.routine import context_at


def decision(
    *,
    button: ClickButton = "left",
    count: int = 1,
    state: PetState | None = None,
    situation: Behaviour | None = None,
    recovering: bool = False,
    recently_petted: bool = False,
) -> ClickDecision:
    stamp = datetime(2026, 10, 12, 15).timestamp()
    return choose_click_reaction(
        button=button,
        click_count=count,
        state=state or PetState(),
        context=context_at(stamp),
        situation=situation,
        recovering=recovering,
        recently_petted=recently_petted,
    )


def busy_situation() -> Behaviour:
    return Behaviour(
        mode="working", strain=55, effort=0.85,
        expected_effort=None, expectation_confident=False,
        present=True, uptime_hours=5,
        prolonged_work_seconds=1800, rest_seconds=0,
        can_sleep=False, should_wake=False, can_nap=False,
    )


class ClickDecisionTests(unittest.TestCase):
    def test_left_right_and_sleeping_are_distinct(self) -> None:
        self.assertEqual(decision().event, "click_left")
        self.assertEqual(decision(button="right").event, "click_right")
        self.assertEqual(
            decision(state=PetState(sleeping=True)).event,
            "sleep_click",
        )

    def test_work_clicks_escalate_to_silence(self) -> None:
        for count, expected in (
            (1, "click_during_work"),
            (3, "click_work_repeat"),
            (5, "click_work_boundary"),
            (7, "click_last_word"),
            (8, None),
        ):
            with self.subTest(count=count):
                self.assertEqual(
                    decision(count=count, situation=busy_situation()).event,
                    expected,
                )

    def test_withdrawn_aiko_stops_at_seven_clicks(self) -> None:
        sad = PetState(mood=20)
        self.assertEqual(decision(count=3, state=sad).event, "click_notice_withdrawn")
        self.assertEqual(decision(count=6, state=sad).event, "click_last_word")
        self.assertIsNone(decision(count=7, state=sad).event)

    def test_cheerful_mood_is_playful_without_irritation(self) -> None:
        happy = PetState(mood=90, energy=75)
        response = decision(count=5, state=happy)
        self.assertEqual(response.event, "click_tease")
        self.assertFalse(response.irritates)

    def test_tired_and_recovering_have_contextual_priority(self) -> None:
        self.assertEqual(
            decision(state=PetState(energy=20)).event, "click_sleepy",
        )
        self.assertEqual(decision(recovering=True).event, "click_after_work")
        self.assertEqual(decision(recently_petted=True).event, "click_flustered")

    def test_low_affection_is_not_social_loneliness(self) -> None:
        self.assertEqual(
            decision(state=PetState(social=20)).event, "click_lonely",
        )
        self.assertEqual(
            decision(state=PetState(affection=20)).event,
            "click_affection_low",
        )

    def test_irritation_only_after_nonplayful_escalation(self) -> None:
        self.assertFalse(decision(count=3).irritates)
        self.assertTrue(decision(count=4).irritates)
        self.assertFalse(decision(count=9).irritates)

    def test_invalid_mouse_button_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            decision(button=cast(ClickButton, "middle"))


if __name__ == "__main__":
    unittest.main()
