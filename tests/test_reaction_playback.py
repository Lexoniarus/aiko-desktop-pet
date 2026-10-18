"""Headless tests for reaction interruption, timing and presentation order."""

from __future__ import annotations

import unittest

from aiko_pet.pet.animation.idle_emote import choose_idle_emote
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.reaction_sequence import Cue
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tools.reaction_test_support import FakeScheduler


class ReactionPlayerTests(unittest.TestCase):
    def test_required_feedback_waits_for_text_and_completes_exactly_once(self):
        done = []
        self.player.play(
            Reaction(
                "id", (Cue.text("Ich schaue es mir an."),), "idle", "object_inspect"
            ),
            2300,
            animate=False,
            on_complete=done.append,
            subject="known-item",
        )
        self.assertEqual(done, [])
        self.assertEqual(self.player.subject, "known-item")
        token = self.active_token()
        delay, stale = self.scheduler.callbacks[token]
        self.assertGreaterEqual(delay, 1800)
        self.scheduler.fire(token)
        stale()
        self.player.cancel()
        self.assertEqual(done, [True])
        self.assertIsNone(self.player.subject)

    def test_cancelled_feedback_cannot_clear_a_new_reactions_timer(self):
        done = []
        self.player.play(
            Reaction("old", (Cue.text("Alt."),), "idle", "object_inspect"),
            on_complete=done.append,
            subject="old-item",
        )
        stale = self.scheduler.callbacks[self.active_token()][1]
        self.player.play(
            Reaction("new", (Cue.text("Neu."),), "idle", "object_recognized"),
            on_complete=done.append,
            subject="new-item",
        )
        current = self.active_token()
        stale()
        self.assertEqual(self.active_token(), current)
        self.assertEqual(self.player.subject, "new-item")
        self.assertEqual(done, [False])
        self.scheduler.fire(current)
        self.assertEqual(done, [False, True])
        self.assertIsNone(self.player.subject)

    def test_unrelated_reaction_drops_subject_even_if_an_old_callback_arrives(self):
        self.player.play(Reaction.spoken("item", "Alt.", "idle", "object_offer"),
                         subject="known-item")
        stale = self.scheduler.callbacks[self.active_token()][1]
        self.player.play(Reaction.spoken("contact", "Hallo.", "idle", "click_left"))
        self.assertIsNone(self.player.subject)
        stale()
        self.assertIsNone(self.player.subject)

    def setUp(self) -> None:
        self.scheduler = FakeScheduler()
        self.rendered: list[tuple[str, str, int]] = []
        self.actions: list[tuple[str, float]] = []
        self.spoken_count = 0
        self.closed = False
        self.player = ReactionPlayer(
            schedule=self.scheduler.schedule,
            cancel_timer=self.scheduler.cancel,
            display_emote=lambda text, duration: self.rendered.append(
                ("emote", text, duration),
            ),
            display_text=lambda text, duration: self.rendered.append(
                ("text", text, duration),
            ),
            start_action=lambda name, duration: self.actions.append(
                (name, duration),
            ),
            mark_spoken=self.note_spoken,
            is_closed=lambda: self.closed,
        )

    def note_spoken(self) -> None:
        self.spoken_count += 1

    def active_token(self) -> str:
        token = self.player.pending_timer
        assert token is not None
        return token

    def test_plain_sequence_uses_reading_time_and_preserves_animation(self) -> None:
        reaction = Reaction(
            "id",
            (
                Cue.text("Oh."),
                Cue.text("Das war unerwartet."),
            ),
            "waiting",
            "click_left",
        )
        self.player.play(reaction)
        self.assertEqual(self.actions, [("waiting", 1.625)])
        self.assertEqual(
            self.rendered, [("text", "Oh.", reaction.beats[0].duration_ms)],
        )
        token = self.active_token()
        self.assertEqual(
            self.scheduler.callbacks[token][0], reaction.beats[0].duration_ms,
        )
        self.scheduler.fire(token)
        self.assertEqual(
            self.rendered[-1],
            ("text", "Das war unerwartet.", reaction.beats[1].duration_ms),
        )
        self.assertIsNotNone(self.player.pending_timer)
        self.assertEqual(self.spoken_count, 2)

    def test_visual_sequence_uses_one_cue_per_timer(self) -> None:
        reaction = Reaction(
            "id",
            (
                Cue("emote", "question", 700),
                Cue.text("Hallo."),
                Cue.text("Noch etwas."),
                Cue("emote", "heart", 900),
            ),
            "waving",
            "click_left",
        )
        self.player.play(reaction, 1700)
        self.assertEqual([item[0] for item in self.rendered], ["emote"])
        self.assertEqual(self.scheduler.callbacks[self.active_token()][0], 700)
        for _ in range(3):
            self.scheduler.fire(self.active_token())
        self.assertEqual(
            [(kind, text) for kind, text, _ in self.rendered],
            [
                ("emote", "question"),
                ("text", "Hallo."),
                ("text", "Noch etwas."),
                ("emote", "heart"),
            ],
        )
        self.scheduler.fire(self.active_token())
        self.assertEqual(self.player.cues, ())
        self.assertIsNone(self.player.pending_timer)

    def test_new_reaction_cancels_stale_followup(self) -> None:
        first = Reaction(
            "old",
            (
                Cue.text("Alt."),
                Cue.text("Zu alt."),
            ),
            "idle",
            "click_left",
        )
        self.player.play(first)
        stale = self.active_token()
        stale_callback = self.scheduler.callbacks[stale][1]
        self.player.play(Reaction("new", (Cue.text("Neu."),), "idle", "click_right"))
        self.assertIn(stale, self.scheduler.cancelled)
        self.assertIsNotNone(self.player.pending_timer)
        stale_callback()
        self.assertEqual(self.rendered[-1][1], "Neu.")
        self.assertEqual(self.spoken_count, 2)

    def test_new_sequence_invalidates_stale_emote_callback(self) -> None:
        self.player.play(
            Reaction(
                "old",
                (
                    Cue("emote", "question", 700),
                    Cue.text("Alt."),
                ),
                "idle",
                "click_left",
            ),
        )
        old = self.active_token()
        stale_callback = self.scheduler.callbacks[old][1]
        self.player.play(Reaction("new", (Cue.text("Neu."),), "idle", "click_right"))
        stale_callback()
        self.assertEqual(
            [(kind, text) for kind, text, _ in self.rendered],
            [("emote", "question"), ("text", "Neu.")],
        )
        self.assertEqual(self.player.cues[0].content, "Neu.")

    def test_cancel_invalidates_the_active_generation(self) -> None:
        self.player.play(Reaction("id", (Cue.text("Hallo."),), "idle", "click_left"))
        before = self.player.generation
        self.player.cancel()
        self.assertEqual(self.player.generation, before + 1)
        self.assertEqual(self.rendered[-1][1], "Hallo.")

    def test_closed_player_does_not_show_stale_followup(self) -> None:
        self.player.play(
            Reaction(
                "id",
                (
                    Cue.text("Hallo."),
                    Cue.text("Später."),
                ),
                "idle",
                "click_left",
            ),
        )
        token = self.active_token()
        self.closed = True
        self.scheduler.fire(token)
        self.assertEqual(len(self.rendered), 1)

    def test_none_reaction_preserves_existing_timers(self) -> None:
        self.player.play(
            Reaction(
                "id",
                (
                    Cue.text("Hallo."),
                    Cue.text("Später."),
                ),
                "idle",
                "click_left",
            ),
        )
        previous = self.player.pending_timer
        generation = self.player.generation
        self.player.play(None)
        self.assertEqual(self.player.pending_timer, previous)
        self.assertEqual(self.player.generation, generation)

    def test_sleeping_suppresses_animation_but_keeps_speech(self) -> None:
        self.player.play(
            Reaction("id", (Cue.text("Guten Morgen."),), "waving", "click_left"),
            animate=False,
        )
        self.assertEqual(self.actions, [])
        self.assertEqual(self.rendered[-1][1], "Guten Morgen.")


class IdleEmoteTests(unittest.TestCase):
    def test_original_threshold_priority_is_preserved(self) -> None:
        self.assertEqual(
            choose_idle_emote(energy=0, satiety=0, mood=0, affection=0),
            "sleeps",
        )
        self.assertEqual(
            choose_idle_emote(energy=20, satiety=0, mood=0, affection=0),
            "drops",
        )
        self.assertEqual(
            choose_idle_emote(energy=20, satiety=18, mood=0, affection=0),
            "faceSad",
        )
        self.assertEqual(
            choose_idle_emote(energy=20, satiety=18, mood=18, affection=0),
            "heart",
        )
        self.assertEqual(
            choose_idle_emote(energy=20, satiety=18, mood=89, affection=18),
            "star",
        )
        self.assertEqual(
            choose_idle_emote(energy=20, satiety=18, mood=88, affection=18),
            "idea",
        )


if __name__ == "__main__":
    unittest.main()
