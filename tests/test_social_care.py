"""Prepared conversations share one domain transition and reward history."""

from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

from test_social_content import fact_payload, joke_payload

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController
from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState


class SocialCareTests(unittest.TestCase):
    def test_variants_commit_once_without_selecting_another_authored_reply(self):
        stamp = datetime(2026, 10, 19, 14).timestamp()
        state = PetState(social=10, energy=80, updated_at=stamp)
        mind = make_aiko_mind(started_at=0)
        adaptive = AdaptiveRoutine()
        controller = CareController(
            state, mind, adaptive, clock=ActiveSessionClock(lambda: 0.0),
        )
        inputs = SessionInputs(
            wall_time=stamp, monotonic_time=100, auto_routine=False,
            allow_bedtime=None, allow_nap=False, interrupt_nap=False, effort=None,
        )
        for index, category in enumerate(SocialCategory):
            payload = (fact_payload() if category == SocialCategory.FACT
                       else joke_payload(category))
            prepared = prepare_social_content(category, payload)
            with patch.object(mind, "select_reaction") as select:
                outcome = controller.execute(
                    CareCommand("talk", conversation=prepared), inputs,
                )
                select.assert_not_called()
            assert outcome.reaction is not None
            completion = outcome.reaction.completed_social
            assert completion is not None
            self.assertEqual(outcome.reaction, replace(
                prepared.reaction, completed_social=completion,
            ))
            self.assertEqual(completion.category, category.value)
            self.assertIsNone(completion.wish_instance_id)
            self.assertIsNotNone(completion.sequence_id)
            self.assertIsNone(prepared.reaction.completed_social)
            self.assertEqual(state.social, 10 + 26 * (index + 1))
            self.assertEqual(state.energy, 80 - (index + 1))
            self.assertEqual(mind._last_care_action, "talk")
            self.assertEqual(adaptive.memory.last_contact_wall, stamp)
            self.assertEqual(len(state.friendship_history.eligible), 0)
        self.assertAlmostEqual(state.friendship, 15)

    def test_preparation_has_no_care_effect_and_other_actions_reject_content(self):
        state = PetState(social=10)
        content = prepare_social_content(SocialCategory.FACT, fact_payload())
        self.assertEqual(state.social, 10)
        self.assertEqual(state.friendship, 15)
        with self.assertRaises(ValueError):
            CareCommand("pet", conversation=content)

    def test_plain_talk_keeps_its_existing_selection(self) -> None:
        state = PetState()
        mind = make_aiko_mind(started_at=0)
        controller = CareController(
            state, mind, AdaptiveRoutine(), clock=ActiveSessionClock(lambda: 0),
        )
        inputs = SessionInputs(
            wall_time=state.updated_at, monotonic_time=100, auto_routine=False,
            allow_bedtime=None, allow_nap=False, interrupt_nap=False, effort=None,
        )
        with patch.object(mind, "select_reaction", return_value=None) as select:
            controller.execute(CareCommand("talk"), inputs)
        select.assert_called_once()
