"""Withholding has clock-driven, bounded consequences, never implicit care."""

import unittest

from aiko_pet.pet.balance import BALANCE, parse_balance
from aiko_pet.pet.catalog_validation import load_json
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook
from aiko_pet.pet.mind.mind import PetMind
from aiko_pet.pet.mind.object_withholding import (
    WithholdingEpisode,
    choose_withholding_response,
)
from aiko_pet.pet.state import PetState


class ObjectWithholdingTests(unittest.TestCase):
    def test_grace_requests_escalation_and_return_do_not_replay_delayed_ticks(self):
        episode = WithholdingEpisode().taken(0)
        self.assertIsNone(choose_withholding_response(episode, 9))
        response = choose_withholding_response(episode, 10)
        assert response is not None
        self.assertEqual(response.event, "object_request_return")
        self.assertEqual(response.friendship_loss, 0)
        response = choose_withholding_response(response.episode, 20)
        assert response is not None
        self.assertTrue(response.irritated)
        self.assertEqual(response.friendship_loss, .15)
        self.assertIsNone(choose_withholding_response(response.episode, 20))
        response = choose_withholding_response(response.episode, 1000)
        assert response is not None
        self.assertAlmostEqual(response.episode.charged_loss, .3)
        self.assertIsNone(choose_withholding_response(response.episode, 1000))
        self.assertIsNone(
            choose_withholding_response(response.episode.returned(), 2000),
        )

    def test_repeated_takes_escalate_and_episode_loss_stays_capped(self):
        episode = WithholdingEpisode().taken(0).returned().taken(1).returned().taken(2)
        response = choose_withholding_response(episode, 12)
        assert response is not None
        self.assertTrue(response.irritated)
        total = response.friendship_loss
        for stamp in range(50, 1000, 40):
            response = choose_withholding_response(response.episode, stamp)
            assert response is not None
            total += response.friendship_loss
        self.assertAlmostEqual(total, .6)

    def test_friendship_loss_preserves_care_history_and_other_irritation(self):
        state = PetState(friendship=.1, friendship_gained_today=5,
                         care_types_today=["feed"], care_last_rewards={"feed": 123})
        self.assertAlmostEqual(state.apply_object_withholding(.15), .1)
        self.assertEqual(state.friendship, 0)
        self.assertEqual(state.friendship_gained_today, 5)
        self.assertEqual(state.care_types_today, ["feed"])
        self.assertEqual(state.care_last_rewards, {"feed": 123})
        for loss in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                state.apply_object_withholding(loss)
        mind = PetMind(DialogueBook.from_file())
        mind.irritated_until = 1000
        mind.note_object_withholding(1)
        self.assertEqual(mind.irritated_until, 1000)

    def test_invalid_withholding_tuning_is_rejected(self):
        for key, value in (("repeated_takes", 0), ("maximum_episode_loss", .01),
                           ("request_interval_seconds", 100)):
            raw = load_json(CATALOGUE.parent / "balance.json")
            raw["object_withholding"][key] = value
            with self.assertRaisesRegex(ValueError, "withholding"):
                parse_balance(raw)
        self.assertGreater(BALANCE.number("object_withholding", "grace_seconds"), 0)
