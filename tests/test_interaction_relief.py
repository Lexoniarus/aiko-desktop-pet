"""Completed helpful actions match impressions without refunding direct loss."""

import unittest
from dataclasses import replace

from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.fun import GameExperience
from aiko_pet.pet.interaction_events import HelpfulInteraction, WithholdingEnded
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tools.reaction_test_support import FakeScheduler


def impressions(*keys):
    return MoodletState(0, len(keys) + 1, tuple(
        MoodletEpisode(i, key, 2, 0, 0, 900,
                       decay_paused=key == MoodletId.WITHHELD)
        for i, key in enumerate(keys, 1)
    ))


class InteractionReliefTests(unittest.TestCase):
    def test_chat_relief_requires_quiet_resolution_and_unused_level(self):
        pet = PetState(lived_seconds=300, moodlets=impressions(
            MoodletId.POKING, MoodletId.CROWDED, MoodletId.WITHHELD,
            MoodletId.DISRUPTED,
        ))
        pet.experience_interaction(HelpfulInteraction("chat"))
        self.assertEqual([e.remaining_seconds for e in pet.moodlets.active],
                         [600, 600, 900, 900])
        previous = pet.moodlets
        pet.experience_interaction(HelpfulInteraction("chat"))
        self.assertEqual(pet.moodlets, previous)
        pet = decode_pet_state(encode_pet_state(pet), now=pet.updated_at)
        pet.experience_interaction(HelpfulInteraction("chat", arrangement_ready=True))
        self.assertEqual([e.remaining_seconds for e in pet.moodlets.active],
                         [600, 600, 900, 600])
        self.assertEqual(pet.friendship, 15)
        pet.experience_interaction(WithholdingEnded())
        pet.experience_interaction(HelpfulInteraction("chat"))
        self.assertEqual(pet.moodlets.active[2].remaining_seconds, 600)

    def test_quiet_gate_and_refusal_deadline_remain_separate(self):
        state = impressions(MoodletId.CROWDED)
        state = replace(state, interactions=replace(
            state.interactions, petting_refused_until=1200,
        ))
        early = PetState(lived_seconds=299, moodlets=state)
        early.experience_interaction(HelpfulInteraction("chat"))
        self.assertEqual(early.moodlets, state)
        pet = PetState(lived_seconds=300, moodlets=state)
        pet.experience_interaction(HelpfulInteraction("chat"))
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 600)
        self.assertEqual(pet.moodlets.interactions.petting_refused_until, 1200)

    def test_api_social_does_not_clear_interpersonal_boundaries(self):
        pet = PetState(lived_seconds=300, moodlets=impressions(
            MoodletId.POKING, MoodletId.CROWDED, MoodletId.DISRUPTED,
        ))
        before = pet.moodlets
        pet.experience_interaction(HelpfulInteraction("social", arrangement_ready=True))
        self.assertEqual(pet.moodlets, before)

    def test_actual_petting_respects_boundary_and_only_relieves_poking(self):
        pet = PetState(affection=10, friendship=50, lived_seconds=300,
                       moodlets=impressions(MoodletId.POKING, MoodletId.CROWDED))
        pet.interact("pet")
        self.assertEqual([e.remaining_seconds for e in pet.moodlets.active], [600, 900])

    def test_shared_play_needs_two_completed_rounds(self):
        pet = PetState(lived_seconds=300, moodlets=impressions(MoodletId.POKING))
        pet.record_game_experience(
            GameExperience("rock_paper_scissors", 1), now=pet.updated_at,
        )
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 900)
        pet.record_game_experience(
            GameExperience("rock_paper_scissors", 2), now=pet.updated_at,
        )
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 600)

    def test_full_sequence_completion_and_cancelled_callbacks(self):
        pet = PetState(lived_seconds=300, moodlets=impressions(MoodletId.POKING))
        scheduler = FakeScheduler()
        completed = []

        def finish(kind):
            completed.append(kind)
            pet.experience_interaction(HelpfulInteraction(kind))

        player = ReactionPlayer(
            schedule=scheduler.schedule, cancel_timer=scheduler.cancel,
            display_emote=lambda *_: None, display_text=lambda *_: None,
            start_action=lambda *_: None, mark_spoken=lambda: None,
            is_closed=lambda: False, social_completed=finish,
        )
        reaction = Reaction("chat", (Cue.text("Eins."), Cue.text("Zwei.")),
                            "idle", "talk", completed_social="chat")
        player.play(reaction)
        token = player.pending_timer
        assert token is not None
        stale = scheduler.callbacks[token][1]
        player.cancel()
        stale()
        self.assertEqual(completed, [])
        player.play(reaction)
        token = player.pending_timer
        assert token is not None
        scheduler.fire(token)
        self.assertEqual(completed, [])  # First bubble is insufficient.
        token = player.pending_timer
        assert token is not None
        stale = scheduler.callbacks[token][1]
        scheduler.fire(token)
        stale()
        self.assertEqual(completed, ["chat"])
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 600)
        player.play(replace(reaction, completed_social=None))
        while player.pending_timer is not None:
            scheduler.fire(player.pending_timer)
        self.assertEqual(completed, ["chat"])  # Ambient dialogue is not human care.

    def test_application_completion_advances_shared_clock_without_second_care(self):
        from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
        from aiko_pet.application.commands import CareCommand
        from aiko_pet.application.controller import CareController
        from aiko_pet.infrastructure.character_mind import make_aiko_mind
        from aiko_pet.pet.mind.adaptive import AdaptiveRoutine

        wall, uptime = 1_800_000_000, [0.0]
        pet = PetState(updated_at=wall, moodlets=MoodletState(0, 2, (
            MoodletEpisode(1, MoodletId.POKING, 1, 0, 0, 1200),
        )))
        controller = CareController(
            pet, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: uptime[0]),
        )
        inputs = SessionInputs(wall, 0, False, None, False, False, None)
        outcome = controller.execute(CareCommand("talk"), inputs)
        assert outcome.reaction is not None
        self.assertEqual(outcome.reaction.completed_social, "chat")
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 1200)
        friendship = pet.friendship
        uptime[0] = 300
        controller.complete_social("chat", replace(inputs, wall_time=wall + 300,
                                                   monotonic_time=300),
                                   arrangement_ready=False)
        self.assertEqual(pet.lived_seconds, 300)
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 600)
        self.assertEqual(pet.friendship, friendship)
        controller.complete_social("chat", replace(inputs, wall_time=wall + 300,
                                                   monotonic_time=300),
                                   arrangement_ready=False)
        self.assertEqual(pet.lived_seconds, 300)
        self.assertEqual(pet.moodlets.active[0].remaining_seconds, 600)
