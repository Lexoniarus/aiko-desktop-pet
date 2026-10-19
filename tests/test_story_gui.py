"""Exercise real Windows/Tk story widgets and their application wiring."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.state import PetState


class StoryGuiTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            probe = tk.Tk()
            probe.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        store = StateStore(Path(directory.name) / "state.json")
        store.save(
            PetState(friendship=90, mood=65, energy=80, social=80, affection=80),
            PetSettings(
                auto_routine=False,
                observe_computer=False,
                auto_walk=False,
            ),
        )
        self.pet = DesktopPet(store=store)
        self.addCleanup(self.pet.quit)
        self.pet._runtime.stop()
        self.pet.root.update()

    def text(self) -> str:
        bubble = self.pet._speech.bubble
        self.assertIsNotNone(bubble)
        assert bubble is not None
        labels = list(bubble.winfo_children())
        while labels:
            widget = labels.pop()
            labels.extend(widget.winfo_children())
            if isinstance(widget, tk.Label) and widget.cget("text"):
                return str(widget.cget("text"))
        return ""

    def click(self) -> None:
        self.pet.canvas.event_generate("<Button-1>", x=90, y=90)
        self.pet.root.update()

    def test_real_talk_bubbles_advance_without_extra_care_or_teasing(self) -> None:
        self.pet.interact("talk")
        player = self.pet._reaction_player
        self.assertTrue(player.story_active)
        texts = [b.content for b in player.cues if b.kind == "text"]
        self.assertEqual(len(texts), 4)
        bond = self.pet.state.friendship
        affection = self.pet.state.affection
        social = self.pet.state.social
        for phrase in texts:
            self.click()
            self.assertEqual(self.text(), phrase)
            self.assertEqual(list(self.pet.mind.clicks), [])
        self.click()
        self.assertFalse(player.story_active)
        self.assertIsNone(self.pet._speech.bubble)
        self.assertEqual(self.pet.state.friendship, bond)
        self.assertEqual(self.pet.state.affection, affection)
        self.assertEqual(self.pet.state.social, social)
        self.click()
        self.assertEqual(len(self.pet.mind.clicks), 1)

    def test_automatic_outputs_wait_even_during_a_blank_pause(self) -> None:
        self.pet.interact("talk")
        player = self.pet._reaction_player
        index = next(i for i, b in enumerate(player.cues) if b.kind == "pause")
        assert player.pending_timer is not None
        self.pet.root.after_cancel(player.pending_timer)
        player._advance(player.generation, index)
        self.assertIsNone(self.pet._speech.bubble)
        recent = tuple(self.pet.mind.book.recent)
        self.pet._attention.last_spoken = -1000000
        self.pet._attention.next_comment = -1000000
        self.pet._action_playback.until = 0
        self.pet._maybe_speak_spontaneously(time.monotonic())
        self.pet._on_cursor_moved(200, 1920, time.monotonic())
        self.pet._on_walk_finished(time.monotonic())
        self.assertEqual(tuple(self.pet.mind.book.recent), recent)
        self.assertTrue(player.story_active)

    def test_care_replaces_story_and_minigame_uses_live_friendship(self) -> None:
        self.pet.interact("talk")
        self.pet.interact("pet")
        self.assertFalse(self.pet._reaction_player.story_active)
        self.pet._hover.open_game()
        self.assertFalse(self.pet._hover.game_open)
        # The next UI action starts after care playback and speech complete.
        # Authored two-bubble care can exceed six seconds; wait for its actual
        # sequence budget instead of assuming one short line was selected.
        deadline = time.monotonic() + 2 + sum(
            cue.duration_ms for cue in self.pet._reaction_player.cues
        ) / 1000
        while (not self.pet._contact.can_interact("play")
               and time.monotonic() < deadline):
            self.pet.root.update()
            time.sleep(.02)
        self.assertTrue(self.pet._contact.can_interact("play"))
        self.pet._hover.open_game()
        chosen = next(
            line
            for line in self.pet.mind.book.lines
            if line.id == self.pet.mind.book.recent[-1]
        )
        self.assertEqual(chosen.event, "game_greeting")
        self.assertEqual(tuple(chosen.stages), ("close",))
        self.assertEqual(self.text(), chosen.text)

    def test_farewell_selects_live_relationship_before_shutdown(self) -> None:
        self.pet._farewell.begin()
        selected = next(
            line
            for line in self.pet.mind.book.lines
            if line.id == self.pet.mind.book.recent[-1]
        )
        self.assertEqual(selected.event, "farewell")
        self.assertEqual(tuple(selected.stages), ("close",))
        self.assertEqual(self.text(), selected.text)
        self.assertFalse(self.pet._closed)
