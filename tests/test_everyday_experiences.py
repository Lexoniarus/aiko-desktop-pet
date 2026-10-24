"""Real completion/gap facts qualify once, independently of need refill."""

import unittest
from dataclasses import replace

from test_wish_assignment import wish
from test_wish_game_assignment import INPUTS, coordinator, finish

from aiko_pet.games.contracts import GameId, GameRoundEvent
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.care_evidence import CareEvidenceState
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.interaction_events import SocialCompletion
from aiko_pet.pet.moodlets import MoodletId, MoodletState
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishId, WishState

WALL = 1800000000


def pet_at(elapsed):
    return PetState(
        updated_at=WALL,
        lived_seconds=elapsed,
        affection=20,
        friendship=60,
        moodlets=MoodletState(care_evidence=CareEvidenceState(0)),
    )


def families(pet):
    return {e.definition_id for e in pet.moodlets.active}


class EverydayExperienceTests(unittest.TestCase):
    def test_social_gap_is_actual_activity_even_when_wish_already_rewarded_it(self):
        pet = pet_at(4 * 3600)
        desired = replace(wish(WishId.CHAT, "chat"), expires_at=20000)
        pet._change(wishes=WishState(2, (desired,)))
        event = SocialCompletion("chat", 1, "first", 4 * 3600)
        pet.complete_social_experience(event)
        self.assertEqual(len(pet.moodlets.active), 1)
        self.assertEqual(pet.moodlets.active[0].level, 1)
        first = pet.capture_checkpoint()
        pet.complete_social_experience(event)
        self.assertEqual(pet.capture_checkpoint(), first)
        pet._change(lived_seconds=5 * 3600)
        pet.complete_social_experience(SocialCompletion("fact", None, "second", 18000))
        self.assertEqual(pet.moodlets.active[0].level, 1)
        pet._change(lived_seconds=9 * 3600)
        pet.complete_social_experience(SocialCompletion("chat", None, "third", 32400))
        self.assertEqual(pet.moodlets.active[0].level, 2)
        saved = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertEqual(saved.moodlets, pet.moodlets)

    def test_no_prior_history_or_incomplete_social_value_invents_gap_credit(self):
        pet = PetState(updated_at=WALL, lived_seconds=50000)
        pet.complete_social_experience(SocialCompletion("chat"))
        self.assertFalse(pet.moodlets.active)
        self.assertIsNone(pet.moodlets.care_evidence)
        pet.complete_social_experience(SocialCompletion("fact", None, "real", 50000))
        self.assertFalse(pet.moodlets.active)

    def test_only_welcome_pet_receives_positive_closeness(self):
        pet = pet_at(14400)
        pet.interact("pet", now=WALL)
        self.assertEqual(families(pet), {MoodletId.SECURE})
        pet.interact("pet", now=WALL)
        self.assertEqual(pet.moodlets.active[0].level, 1)
        self.assertEqual(len(pet.moodlets.care_evidence.encounters), 1)
        pet._change(lived_seconds=28800, affection=100, friendship=10)
        pet.interact("pet", now=WALL)  # Tolerated excess is not welcome closeness.
        self.assertEqual(pet.moodlets.active[0].level, 1)
        self.assertEqual(len(pet.moodlets.care_evidence.encounters), 1)

    def test_two_round_session_after_gap_and_comeback_are_different_real_events(self):
        pet = pet_at(10000)
        runtime = coordinator(pet)
        for number, result in ((1, "win"), (2, "win"), (3, "loss")):
            event = GameRoundEvent(GameId.BLACKJACK, "actual", number)
            runtime.observe_round(event, INPUTS)
            finish(runtime, event, result)
        self.assertEqual(families(pet), {MoodletId.PRIDE})
        runtime.complete(GameExperience("blackjack", 3, 1, 0, 2), INPUTS)
        # The last comeback round is not rewarded again as shared play.
        self.assertEqual(families(pet), {MoodletId.PRIDE})
        self.assertEqual(len(pet.moodlets.care_evidence.encounters), 1)
        saved = decode_pet_state(encode_pet_state(pet), now=WALL)
        self.assertEqual(saved.moodlets, pet.moodlets)

    def test_session_requires_actual_two_rounds_and_complete_callback(self):
        pet = pet_at(10000)
        runtime = coordinator(pet)
        event = GameRoundEvent(GameId.MASTERMIND, "actual", 1)
        runtime.observe_round(event, INPUTS)
        finish(runtime, event, "draw")
        runtime.complete(GameExperience("mastermind", 1, 0, 1, 0), INPUTS)
        self.assertFalse(pet.moodlets.active)
        pet._change(lived_seconds=20000)
        for n in (1, 2):
            event = GameRoundEvent(GameId.MASTERMIND, "other", n)
            runtime.observe_round(event, INPUTS)
            finish(runtime, event, "draw")
        self.assertFalse(pet.moodlets.active)
        runtime.complete(GameExperience("mastermind", 2, 0, 2, 0), INPUTS)
        self.assertEqual(families(pet), {MoodletId.SHARED_PLAY})
        before = pet.moodlets
        pet.complete_play_session(
            game_id="mastermind", session_id="other", round_id="other:2"
        )
        self.assertEqual(pet.moodlets, before)


if __name__ == "__main__":
    unittest.main()
