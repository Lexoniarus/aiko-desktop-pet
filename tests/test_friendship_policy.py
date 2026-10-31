"""Real contact, continuous emotional flow and one-time policy migration."""
import unittest
from dataclasses import replace

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.consumption import ConsumptionOrigin
from aiko_pet.pet.friendship_decay import advance_friendship, balance_friendship
from aiko_pet.pet.friendship_history import FriendshipHistory, FriendshipProgress
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.state import PetState

START = 1800000000.
HEALTHY = (100.,) * 5


class FriendshipPolicyTests(unittest.TestCase):
    def test_accepted_care_renews_contact_without_instant_points_or_reward_pots(self):
        pet = PetState(affection=10, satiety=30, energy=30, friendship=56,
                       updated_at=START)
        for action in ('pet', 'feed', 'talk', 'energy_drink'):
            pet.interact(action, now=START)
            self.assertEqual(pet.friendship, 56)
            self.assertEqual(pet.friendship_history.last_contact, 0)
            self.assertFalse(pet.friendship_history.rewards)
            self.assertFalse(pet.friendship_history.eligible)
        self.assertFalse(pet.care_last_rewards)

    def test_autonomous_intake_and_unplayed_games_do_not_create_contact(self):
        pet = PetState(satiety=100, energy=100, updated_at=START)
        for action in ('feed', 'energy_drink', 'play'):
            pet.interact(action, now=START)
        self.assertIsNone(pet.friendship_history.last_contact)
        pet = PetState(satiety=30, updated_at=START)
        pet.consume_item('apple', ConsumptionOrigin.AUTONOMOUS, now=START)
        self.assertIsNone(pet.friendship_history.last_contact)
        for units in (0, 1, 2):
            pet = PetState(updated_at=START)
            pet.record_game_experience(GameExperience('rock_paper_scissors', units),
                                       now=START)
            self.assertEqual(pet.friendship, 15)
            self.assertEqual(pet.friendship_history.last_contact,
                             None if units == 0 else 0)

    def test_contact_expiry_inside_interval_splits_positive_and_absence_flow(self):
        history = FriendshipHistory(0, last_contact=0, continuous_since=0)
        result = advance_friendship(FriendshipProgress(70, history, 14385), 30,
                                    HEALTHY, HEALTHY, sleeping=False,
                                    mood_before=80, mood_after=80)
        expected = balance_friendship(70, positive=.001, negative=0)
        expected = balance_friendship(expected, positive=0, negative=.5 * 15 / 3600)
        self.assertAlmostEqual(result.points, expected, places=10)

    def test_positive_mood_requires_contact_but_negative_emotions_do_not(self):
        progress = FriendshipProgress(70, FriendshipHistory(0, continuous_since=0), 0)
        healthy = advance_friendship(progress, 30, HEALTHY, HEALTHY, sleeping=False,
                                     mood_before=80, mood_after=80)
        self.assertEqual(healthy.points, 70)
        moodlets = MoodletState(active=(
            MoodletEpisode(1, MoodletId.DISAPPOINTED, 1, 0, 0, 1800),
        ))
        upset = advance_friendship(progress, 30, HEALTHY, HEALTHY,
                                   moodlets=moodlets, sleeping=False,
                                   mood_before=80, mood_after=80)
        self.assertAlmostEqual(upset.points,
                               balance_friendship(70, positive=0, negative=.006))

    def test_old_save_activates_at_catchup_endpoint_without_refund_or_contact(self):
        pet = PetState(updated_at=START, friendship=56, satiety=100, energy=100,
                       fun=100, social=100, affection=100)
        raw = encode_pet_state(pet)
        raw['relationship'].pop('continuous_since')
        restored = decode_pet_state(raw, now=START)
        self.assertIsNone(restored.friendship_history.continuous_since)
        restored.advance(START + 60, observed=False)
        self.assertEqual(restored.friendship, 56)
        self.assertEqual(restored.friendship_history.continuous_since, 60)
        self.assertIsNone(restored.friendship_history.last_contact)
        again = decode_pet_state(encode_pet_state(restored), now=START + 60)
        self.assertEqual(again.friendship_history, restored.friendship_history)
        again.anchor_live_session(START + 120)
        self.assertEqual(again.friendship_history.continuous_since, 60)

    def test_partial_moodlet_lifetime_is_not_charged_after_expiry(self):
        pet = PetState(updated_at=START, friendship=50, mood=50, satiety=80,
                       energy=80, fun=80, social=80, affection=80,
                       moodlets=MoodletState(active=(
                           MoodletEpisode(1, MoodletId.DISAPPOINTED, 1, 0, 0, 7),
                       )))
        pet.advance(START + 30)
        self.assertFalse(pet.moodlets.active)
        self.assertAlmostEqual(pet.friendship, balance_friendship(
            50, positive=0, negative=.006 * 7 / 30), places=9)

    def test_tier_change_inside_interval_uses_both_actual_intensities(self):
        pet = PetState(updated_at=START, friendship=50, mood=50, satiety=80,
                       energy=80, fun=80, social=80, affection=80,
                       moodlets=MoodletState(active=(
                           MoodletEpisode(1, MoodletId.SECURE, 2, 0, 0, 10),
                       )))
        pet.advance(START + 30)
        expected = balance_friendship(50, positive=.006 * 10 / 30, negative=0)
        expected = balance_friendship(expected, positive=.003 * 20 / 30, negative=0)
        self.assertAlmostEqual(pet.friendship, expected, places=9)
        self.assertEqual(pet.moodlets.active[0].level, 1)

    def test_closed_save_partition_preserves_unrounded_values(self):
        pet = PetState(updated_at=START, friendship=70, mood=65, satiety=90,
                       energy=90, fun=90, social=90, affection=90)
        pet.restore_checkpoint(replace(pet.capture_checkpoint(), relationship=replace(
            pet.friendship_history, last_contact=0)))
        whole = decode_pet_state(encode_pet_state(pet), now=START)
        whole.advance(START + 60, observed=False)
        for end in (30, 60):
            pet.advance(START + end, observed=False)
            pet = decode_pet_state(encode_pet_state(pet), now=START + end)
        for name in ('friendship', 'satiety', 'mood', 'energy', 'social', 'affection'):
            self.assertAlmostEqual(getattr(pet, name), getattr(whole, name), places=9)
