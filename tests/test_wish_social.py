"""Only complete admitted dialogue/content can fulfill the captured social wish."""

import random
import unittest
from dataclasses import replace

from test_social_content import fact_payload, joke_payload
from test_social_sayings import quotation, quote_payload

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController
from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletId
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tools.reaction_test_support import FakeScheduler

WALL = 1800000000.0


def wishes(key, instance=1):
    return WishState(
        instance + 1,
        (ActiveWish(instance, key, key.value, 0, 14400),),
        ((WishArea.SOCIAL, 0),),
    )


class SocialWishTests(unittest.TestCase):
    def make(self, key):
        self.pet = PetState(
            updated_at=WALL,
            lived_seconds=100,
            social=90,
            friendship=50,
            wishes=wishes(key),
        )
        self.inputs = SessionInputs(WALL, 0, False, None, False, False, None)
        self.controller = CareController(
            self.pet,
            make_aiko_mind(started_at=0, rng=random.Random(7)),
            AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )
        self.scheduler = FakeScheduler()
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule,
            cancel_timer=self.scheduler.cancel,
            display_emote=lambda *_: None,
            display_text=lambda *_: None,
            start_action=lambda *_: None,
            mark_spoken=lambda: None,
            is_closed=lambda: False,
            social_completed=self.finish,
        )

    def finish(self, completion):
        self.controller.complete_social(
            completion, self.inputs, arrangement_ready=False
        )

    def execute(self, key):
        content = None
        if key != WishId.CHAT:
            category = SocialCategory(key.value)
            payload = fact_payload() if key == WishId.FACT else joke_payload(category)
            content = prepare_social_content(category, payload)
        outcome = self.controller.execute(
            CareCommand("talk", conversation=content), self.inputs
        )
        assert outcome.reaction is not None
        return outcome.reaction

    def complete_playback(self):
        while self.player.pending_timer is not None:
            self.scheduler.fire(self.player.pending_timer)

    def test_all_four_categories_wait_for_whole_sequence_and_fulfill_once(self):
        for key, moodlet in (
            (WishId.CHAT, MoodletId.CONNECTION),
            (WishId.SINGLE, MoodletId.CHEERFUL),
            (WishId.TWO_PARTS, MoodletId.CHEERFUL),
            (WishId.FACT, MoodletId.ENTHUSIASTIC),
        ):
            self.make(key)
            reaction = self.execute(key)
            assert reaction.completed_social is not None
            self.assertEqual((reaction.completed_social.category,
                              reaction.completed_social.wish_instance_id),
                             (key.value, 1))
            self.assertEqual(reaction.completed_social.started_at, 100)
            self.assertIsNotNone(reaction.completed_social.sequence_id)
            self.assertTrue(self.pet.wishes.active)
            self.assertFalse(self.pet.moodlets.active)
            self.assertEqual(self.pet.friendship, 50)
            self.player.play(reaction)
            self.assertTrue(self.pet.wishes.active)  # First bubble is not completion.
            self.complete_playback()
            self.assertFalse(self.pet.wishes.active)
            self.assertEqual(self.pet.moodlets.active[0].definition_id, moodlet)
            self.assertEqual(self.pet.friendship, 50)
            loaded = decode_pet_state(encode_pet_state(self.pet), now=WALL)
            completion = reaction.completed_social
            assert completion is not None
            loaded.complete_social_experience(completion)
            self.assertEqual(loaded.moodlets.active, self.pet.moodlets.active)
            self.assertEqual(loaded.friendship, 50)

    def test_interrupted_joke_and_stale_callback_preserve_wish_and_ordinary_care(self):
        self.make(WishId.TWO_PARTS)
        self.player.play(self.execute(WishId.TWO_PARTS))
        token = self.player.pending_timer
        assert token is not None
        stale = self.scheduler.callbacks[token][1]
        self.player.cancel()
        stale()
        self.assertTrue(self.pet.wishes.active)
        self.assertFalse(self.pet.moodlets.active)
        self.assertEqual(self.pet.friendship, 50)

    def test_quote_wish_waits_for_author_without_an_extra_reward(self):
        for cancel in (False, True):
            self.make(WishId.SINGLE)
            outcome = self.controller.execute(
                CareCommand("talk", conversation=quotation(quote_payload())),
                self.inputs,
            )
            reaction = outcome.reaction
            assert reaction is not None and reaction.completed_social is not None
            self.assertEqual((reaction.completed_social.category,
                              reaction.completed_social.wish_instance_id),
                             ("single", 1))
            social, energy = self.pet.social, self.pet.energy
            self.player.play(reaction)
            # Advance introduction and body: author credit is now being read.
            for _ in range(2):
                assert self.player.pending_timer is not None
                self.scheduler.fire(self.player.pending_timer)
            self.assertTrue(self.pet.wishes.active)
            self.assertFalse(self.pet.moodlets.active)
            if cancel:
                token = self.player.pending_timer
                assert token is not None
                stale = self.scheduler.callbacks[token][1]
                self.player.cancel()
                stale()
                self.assertTrue(self.pet.wishes.active)
                self.assertFalse(self.pet.moodlets.active)
            else:
                self.complete_playback()
                self.assertFalse(self.pet.wishes.active)
                self.assertEqual(self.pet.moodlets.active[0].definition_id,
                                 MoodletId.CHEERFUL)
                moodlets = self.pet.moodlets.active
                self.finish(reaction.completed_social)
                self.assertEqual(self.pet.moodlets.active, moodlets)
            self.assertEqual((self.pet.social, self.pet.energy), (social, energy))
            self.assertEqual(self.pet.friendship, 50)

    def test_wish_created_during_conversation_is_not_retrospectively_adopted(self):
        self.make(WishId.CHAT)
        self.pet.restore_checkpoint(
            replace(self.pet.capture_checkpoint(), wishes=WishState())
        )
        reaction = self.execute(WishId.CHAT)
        self.pet.restore_checkpoint(
            replace(self.pet.capture_checkpoint(), wishes=wishes(WishId.CHAT))
        )
        self.player.play(reaction)
        self.complete_playback()
        self.assertTrue(self.pet.wishes.active)
        self.assertFalse(self.pet.moodlets.active)

    def test_expired_or_replaced_identity_is_not_fulfilled_by_old_playback(self):
        for replacement in (None, wishes(WishId.FACT, 2)):
            self.make(WishId.FACT)
            reaction = self.execute(WishId.FACT)
            checkpoint = self.pet.capture_checkpoint()
            self.pet.restore_checkpoint(
                replace(
                    checkpoint,
                    lived_seconds=14400 if replacement is None else 100,
                    wishes=checkpoint.wishes if replacement is None else replacement,
                )
            )
            self.player.play(reaction)
            self.complete_playback()
            self.assertEqual(bool(self.pet.wishes.active), replacement is not None)
            self.assertFalse(self.pet.moodlets.active)
            self.assertEqual(self.pet.friendship, 50)

    def test_other_category_does_not_fulfill_and_single_twopart_share_one_family(self):
        self.make(WishId.SINGLE)
        self.player.play(self.execute(WishId.FACT))
        self.complete_playback()
        self.assertTrue(self.pet.wishes.active)
        self.player.play(self.execute(WishId.SINGLE))
        self.complete_playback()
        self.pet.restore_checkpoint(
            replace(self.pet.capture_checkpoint(), wishes=wishes(WishId.TWO_PARTS, 2))
        )
        self.player.play(self.execute(WishId.TWO_PARTS))
        self.complete_playback()
        self.assertEqual(len(self.pet.moodlets.active), 1)
        self.assertEqual(self.pet.moodlets.active[0].definition_id, MoodletId.CHEERFUL)
        self.assertEqual(self.pet.moodlets.active[0].level, 2)
        self.assertEqual(self.pet.moodlets.active[0].remaining_seconds, 2700)
        self.assertLessEqual(
            sum(e.amount for e in self.pet.friendship_history.rewards), 0.75
        )
