"""Sleeping contact counts deliberate pokes without inventing care or energy."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.dialogue_context import FriendshipStage
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from tools.pet_test_support import set_test_pet_values


class SleepClickTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wall = datetime(2026, 10, 20, 23).timestamp()
        self.state = PetState(sleeping=True, energy=8, updated_at=self.wall)
        self.mind = make_aiko_mind(started_at=0)
        self.adaptive = AdaptiveRoutine()
        self.controller = CareController(
            self.state, self.mind, self.adaptive,
            clock=ActiveSessionClock(lambda: 0.0),
        )
        self.inputs = SessionInputs(
            wall_time=self.wall, monotonic_time=100,
            auto_routine=False, allow_bedtime=None, allow_nap=False,
            interrupt_nap=False, effort=None,
        )
        self.context = context_at(self.wall)

    def test_fourth_sleep_click_requests_waking_without_mutating_pet(self) -> None:
        checkpoint = self.state.capture_checkpoint()
        for index in range(4):
            reaction = self.mind.click(
                "left", self.state, self.context, 10 + index / 10,
            )
            self.assertEqual(self.mind.click_wakes, index == 3)
            if index < 3:
                assert reaction is not None
                self.assertEqual(reaction.event, "sleep_click")
            else:
                self.assertIsNone(reaction)
        self.assertEqual(self.state.capture_checkpoint(), checkpoint)

    def test_awake_clicks_do_not_count_toward_new_sleep_disturbance(self) -> None:
        set_test_pet_values(self.state, sleeping=False)
        for index in range(3):
            self.mind.click("left", self.state, self.context, 10 + index / 10)
        set_test_pet_values(self.state, sleeping=True)
        self.mind.click("right", self.state, self.context, 10.3)
        self.assertFalse(self.mind.click_wakes)
        self.assertEqual(len(self.mind.clicks), 1)

    def test_click_wake_grants_no_energy_care_credit_or_durable_contact(self) -> None:
        history = self.state.friendship_history
        needs = (self.state.energy, self.state.social, self.state.affection)
        outcome = self.controller.execute(
            CareCommand("sleep", wake_from_clicks=True), self.inputs,
        )
        self.assertFalse(self.state.sleeping)
        self.assertEqual((self.state.energy, self.state.social, self.state.affection),
                         needs)
        self.assertEqual(self.state.friendship_history, history)
        self.assertEqual(self.mind._last_care_at, -1)
        self.assertEqual(self.mind.emotion(self.state, 100), "irritated")
        assert outcome.reaction is not None
        self.assertEqual(outcome.reaction.event, "click_wake")
        self.state.advance(self.wall + 29 * 60, auto_routine=True)
        self.assertFalse(self.state.sleeping)
        self.state.advance(self.wall + 30 * 60, auto_routine=True)
        self.assertTrue(self.state.sleeping)

    def test_click_wake_is_idempotent_if_sleep_ended_before_dispatch(self) -> None:
        set_test_pet_values(self.state, sleeping=False)
        self.controller.execute(
            CareCommand("sleep", wake_from_clicks=True), self.inputs,
        )
        self.assertFalse(self.state.sleeping)

    def test_sleep_can_end_during_time_progress_without_toggling_back(self) -> None:
        set_test_pet_values(self.state, energy=100)
        self.state.interact("sleep", now=self.wall)  # End the initial legacy sleep.
        self.state.interact("sleep", now=self.wall)
        inputs = replace(self.inputs,
                         wall_time=datetime(2026, 10, 21, 8).timestamp())
        ticks = iter((0.0, 9 * 3600.0))
        controller = CareController(
            self.state, self.mind, self.adaptive,
            clock=ActiveSessionClock(lambda: next(ticks)),
        )
        with patch.object(self.state, "interact", wraps=self.state.interact) as toggle:
            controller.execute(CareCommand("sleep", wake_from_clicks=True), inputs)
        toggle.assert_not_called()
        self.assertFalse(self.state.sleeping)

    def test_rough_wake_command_cannot_be_used_for_other_care(self) -> None:
        for action in ("pet", "talk", "feed"):
            with self.subTest(action=action), self.assertRaises(ValueError):
                CareCommand.from_action(action, wake_from_clicks=True)

    def test_each_friendship_stage_has_distinct_rough_wake_feedback(self) -> None:
        context = self.mind.dialogue_context(self.state, self.context, 10)
        for stage in FriendshipStage:
            texts = set()
            for index in range(3):
                reaction = self.mind.select_reaction(
                    "click_wake", self.state, self.context, 100 + index,
                    dialogue=replace(context, stage=stage, mood="irritated"),
                )
                assert reaction is not None
                texts.add(reaction.text)
                self.assertIn(stage.value, reaction.line_id)
                self.assertEqual(reaction.beats[0].kind, "text")
                self.assertEqual(reaction.beats[-1].content, "anger")
            self.assertEqual(len(texts), 3)
