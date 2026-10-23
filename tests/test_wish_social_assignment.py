"""Captured social identity completes once, after the entire admitted sequence."""

import unittest
from dataclasses import replace

from test_social_content import fact_payload, joke_payload
from test_wish_assignment import wish

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.commands import CareCommand
from aiko_pet.application.controller import CareController
from aiko_pet.application.social_content import SocialCategory, prepare_social_content
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.interaction_events import SocialCompletion
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import WishArea, WishId, WishState, WishTargetMode
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tools.reaction_test_support import FakeScheduler

WALL = 1800000000


class SocialHarness:
    def __init__(self, *wishes):
        self.pet = PetState(
            updated_at=WALL, lived_seconds=100, friendship=50, social=50,
            wishes=WishState(max((w.instance_id for w in wishes), default=0) + 1,
                             wishes, ((WishArea.SOCIAL, 0),) if wishes else (),
                             refresh_at=600),
        )
        self.inputs = SessionInputs(WALL, 0, False, None, False, False, None)
        self.controller = CareController(
            self.pet, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        )
        self.scheduler = FakeScheduler()
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule, cancel_timer=self.scheduler.cancel,
            display_emote=lambda *_: None, display_text=lambda *_: None,
            start_action=lambda *_: None, mark_spoken=lambda: None,
            is_closed=lambda: False,
            social_completed=lambda completion: self.controller.complete_social(
                completion, self.inputs, arrangement_ready=False,
            ),
        )

    def admit(self, category="chat"):
        content = None
        if category != "chat":
            kind = SocialCategory(category)
            content = prepare_social_content(
                kind, fact_payload() if category == "fact" else joke_payload(kind),
            )
        reaction = self.controller.execute(
            CareCommand("talk", conversation=content), self.inputs,
        ).reaction
        assert reaction is not None
        self.player.play(reaction)
        return reaction.completed_social

    def finish(self):
        while self.player.pending_timer is not None:
            self.scheduler.fire(self.player.pending_timer)


class AssignedSocialWishTests(unittest.TestCase):
    def test_free_social_wish_accepts_each_supported_complete_sequence(self):
        for category in ("chat", "single", "twopart", "fact"):
            with self.subTest(category=category):
                harness = SocialHarness(wish(WishId.SOCIAL_ANY))
                completion = harness.admit(category)
                self.assertEqual(completion.wish_instance_id, 1)
                self.assertTrue(harness.pet.wishes.active)
                self.assertFalse(harness.pet.moodlets.active)
                self.assertIsNone(harness.pet.moodlets.care_evidence)
                social, energy = harness.pet.social, harness.pet.energy
                harness.finish()
                self.assertFalse(harness.pet.wishes.active)
                episode = harness.pet.moodlets.active[0]
                self.assertEqual(episode.definition_id, MoodletId.CONNECTION)
                cause = episode.causes[0]
                self.assertEqual(cause.wish.target.mode, WishTargetMode.ANY)
                self.assertEqual(cause.target_id, category)
                self.assertEqual(cause.event_id, f"social:{completion.sequence_id}")
                self.assertEqual((harness.pet.social, harness.pet.energy),
                                 (social, energy))
                self.assertEqual(harness.pet.friendship, 50)
                loaded = decode_pet_state(encode_pet_state(harness.pet), now=WALL)
                self.assertEqual(loaded.moodlets, harness.pet.moodlets)

    def test_concrete_category_wins_and_free_wish_receives_no_duplicate(self):
        free = wish(WishId.SOCIAL_ANY)
        fact = wish(WishId.FACT, "fact", instance=2)
        harness = SocialHarness(free, fact)
        completion = harness.admit("fact")
        self.assertEqual(completion.wish_instance_id, 2)
        harness.finish()
        self.assertEqual(harness.pet.wishes.active, (free,))
        self.assertEqual(harness.pet.moodlets.active[0].definition_id,
                         MoodletId.ENTHUSIASTIC)

    def test_pinned_free_wish_wins_and_keeps_assignment_during_playback(self):
        free = wish(WishId.SOCIAL_ANY, pinned=True)
        fact = wish(WishId.FACT, "fact", instance=2)
        harness = SocialHarness(fact, free)
        completion = harness.admit("fact")
        self.assertEqual(completion.wish_instance_id, 1)
        harness.pet.set_wish_pinned(1, False)
        harness.pet.set_wish_pinned(2, True)
        harness.finish()
        self.assertEqual([w.instance_id for w in harness.pet.wishes.active], [2])
        self.assertEqual(harness.pet.moodlets.active[0].definition_id,
                         MoodletId.CONNECTION)

    def test_interruption_and_queued_callback_produce_no_completion_receipt(self):
        harness = SocialHarness(wish(WishId.SOCIAL_ANY))
        harness.admit("twopart")
        token = harness.player.pending_timer
        stale = harness.scheduler.callbacks[token][1]
        before = harness.pet.capture_checkpoint()
        harness.player.cancel()
        stale()
        self.assertEqual(harness.pet.capture_checkpoint(), before)
        self.assertIsNone(harness.pet.moodlets.care_evidence)

    def test_dismissed_specific_assignment_does_not_fall_back_to_free_wish(self):
        free = wish(WishId.SOCIAL_ANY)
        fact = wish(WishId.FACT, "fact", instance=2)
        harness = SocialHarness(free, fact)
        harness.admit("fact")
        harness.pet.dismiss_wish(2)
        harness.finish()
        self.assertEqual(harness.pet.wishes.active, (free,))
        self.assertFalse(harness.pet.moodlets.active)
        self.assertEqual(len(harness.pet.moodlets.care_evidence.experiences), 1)

    def test_unassigned_sequence_cannot_adopt_a_later_created_wish(self):
        harness = SocialHarness()
        completion = harness.admit("chat")
        self.assertIsNone(completion.wish_instance_id)
        later = wish(WishId.SOCIAL_ANY, at=100)
        harness.pet.restore_checkpoint(replace(harness.pet.capture_checkpoint(),
                                               wishes=WishState(
                                                   2, (later,),
                                                   ((WishArea.SOCIAL, 100),),
                                                   refresh_at=600,
                                               )))
        harness.finish()
        self.assertEqual(harness.pet.wishes.active, (later,))
        self.assertFalse(harness.pet.moodlets.active)

    def test_repeated_completion_after_reload_cannot_repeat_relief_or_reward(self):
        harness = SocialHarness(wish(WishId.SOCIAL_ANY))
        harness.pet.restore_checkpoint(replace(harness.pet.capture_checkpoint(),
                                               moodlets=MoodletState(0, 2, (
                                                   MoodletEpisode(1, MoodletId.POKING,
                                                                  1, 0, 0, 1200),
                                               ))))
        completion = harness.admit("chat")
        harness.finish()
        loaded = decode_pet_state(encode_pet_state(harness.pet), now=WALL)
        # Even after the relief cooldown, this actual sequence remains consumed.
        loaded.restore_checkpoint(replace(loaded.capture_checkpoint(),
                                          lived_seconds=2000))
        before = loaded.capture_checkpoint()
        loaded.complete_social_experience(completion)
        self.assertEqual(loaded.capture_checkpoint(), before)

    def test_distinct_admissions_share_category_without_reusing_identity(self):
        harness = SocialHarness(wish(WishId.SOCIAL_ANY))
        first = harness.admit("chat")
        harness.finish()
        next_wish = wish(WishId.SOCIAL_ANY, instance=2, at=100)
        harness.pet.restore_checkpoint(replace(harness.pet.capture_checkpoint(),
                                               wishes=WishState(
                                                   3, (next_wish,),
                                                   ((WishArea.SOCIAL, 100),),
                                                   refresh_at=600,
                                               )))
        second = harness.admit("chat")
        self.assertNotEqual(first.sequence_id, second.sequence_id)
        harness.finish()
        episode = harness.pet.moodlets.active[0]
        self.assertEqual(episode.level, 2)
        self.assertEqual(len(episode.causes), 2)
        self.assertEqual(len(harness.pet.moodlets.care_evidence.experiences), 2)

    def test_admission_metadata_requires_paired_finite_fields(self):
        for values in ({"sequence_id": "actual"}, {"started_at": 0},
                       {"sequence_id": "", "started_at": 0},
                       {"sequence_id": "actual", "started_at": -1},
                       {"sequence_id": "actual", "started_at": float("nan")}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                SocialCompletion("chat", **values)
