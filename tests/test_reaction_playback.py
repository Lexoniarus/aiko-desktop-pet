"""Headless tests for reaction interruption, timing and presentation order."""

from __future__ import annotations

import unittest
from collections.abc import Callable

from aiko_pet.pet.animation.idle_emote import choose_idle_emote
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer


class FakeScheduler:
    def __init__(self) -> None:
        self.callbacks: dict[str, tuple[int, Callable[[], None]]] = {}
        self.cancelled: set[str] = set()
        self.next_id = 0

    def schedule(self, delay_ms: int, callback: Callable[[], None]) -> str:
        self.next_id += 1
        token = str(self.next_id)
        self.callbacks[token] = (delay_ms, callback)
        return token

    def cancel(self, token: str) -> None:
        self.cancelled.add(token)
        self.callbacks.pop(token, None)

    def fire(self, token: str) -> None:
        _, callback = self.callbacks.pop(token)
        callback()


class ReactionPlayerTests(unittest.TestCase):
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

    def test_plain_reaction_preserves_followup_delay_and_animation(self) -> None:
        reaction = Reaction(
            "id", "Oh.", "waiting", "click_left",
            "Das war unerwartet.", 600,
        )
        self.player.play(reaction)
        self.assertEqual(self.actions, [("waiting", 1.625)])
        self.assertEqual(self.rendered, [("text", "Oh.", 2600)])
        token = self.active_token()
        self.assertEqual(self.scheduler.callbacks[token][0], 600)
        self.scheduler.fire(token)
        self.assertEqual(self.rendered[-1], ("text", "Das war unerwartet.", 2600))
        self.assertIsNone(self.player.pending_timer)
        self.assertEqual(self.spoken_count, 2)

    def test_visual_sequence_uses_one_cue_per_timer(self) -> None:
        reaction = Reaction(
            "id", "Hallo.", "waving", "click_left",
            "Noch etwas.", 900, "question", "heart",
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
        first = Reaction("old", "Alt.", "idle", "click_left", "Zu alt.", 600)
        self.player.play(first)
        stale = self.active_token()
        stale_callback = self.scheduler.callbacks[stale][1]
        self.player.play(Reaction("new", "Neu.", "idle", "click_right"))
        self.assertIn(stale, self.scheduler.cancelled)
        self.assertEqual(self.player.pending_timer, None)
        stale_callback()
        self.assertEqual(self.rendered[-1][1], "Neu.")
        self.assertEqual(self.spoken_count, 2)

    def test_new_sequence_invalidates_stale_emote_callback(self) -> None:
        self.player.play(
            Reaction("old", "Alt.", "idle", "click_left", None, 900, "question"),
        )
        old = self.active_token()
        stale_callback = self.scheduler.callbacks[old][1]
        self.player.play(Reaction("new", "Neu.", "idle", "click_right"))
        stale_callback()
        self.assertEqual(
            [(kind, text) for kind, text, _ in self.rendered],
            [("emote", "question"), ("text", "Neu.")],
        )
        self.assertEqual(self.player.cues, ())

    def test_cancel_increments_generation_without_erasing_bubble(self) -> None:
        self.player.play(Reaction("id", "Hallo.", "idle", "click_left"))
        before = self.player.generation
        self.player.cancel()
        self.assertEqual(self.player.generation, before + 1)
        self.assertEqual(self.rendered[-1][1], "Hallo.")

    def test_closed_player_does_not_show_stale_followup(self) -> None:
        self.player.play(
            Reaction("id", "Hallo.", "idle", "click_left", "Später.", 600),
        )
        token = self.active_token()
        self.closed = True
        self.scheduler.fire(token)
        self.assertEqual(len(self.rendered), 1)

    def test_none_reaction_preserves_existing_timers(self) -> None:
        self.player.play(
            Reaction("id", "Hallo.", "idle", "click_left", "Später.", 600),
        )
        previous = self.player.pending_timer
        generation = self.player.generation
        self.player.play(None)
        self.assertEqual(self.player.pending_timer, previous)
        self.assertEqual(self.player.generation, generation)

    def test_sleeping_suppresses_animation_but_keeps_speech(self) -> None:
        self.player.play(
            Reaction("id", "Guten Morgen.", "waving", "click_left"),
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
