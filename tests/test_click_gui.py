"""Direct sprite input reaches teasing while real interactions stay exclusive."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.state import PetState
from tools.desktop_test_support import create_test_desktop
from tools.persistence_test_support import save_test_session
from tools.tk_test_time import ControlledTkTime


class ClickGuiTests(unittest.TestCase):
    def setUp(self) -> None:
        try:
            probe = tk.Tk()
            probe.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.timing = self.enterContext(ControlledTkTime())
        directory = tempfile.TemporaryDirectory(prefix="aiko-click-test-")
        self.addCleanup(directory.cleanup)
        store = StateStore(Path(directory.name) / "state.json")
        save_test_session(store,
            PetState(friendship=50, mood=60, energy=80, social=75, affection=75),
            PetSettings(auto_routine=False, observe_computer=False, auto_walk=False,
                        spontaneous_talk=False, learn_rhythm=False),
        )
        self.pet = create_test_desktop(store=store)
        self.addCleanup(self.pet.quit)
        self.pet._runtime.stop()
        self.pet.root.update()
        self.pet._activity.advance_state(time.time())

    def click(self, button: int = 1) -> None:
        self.pet.canvas.event_generate(f"<Button-{button}>", x=90, y=90)
        self.pet.root.update()

    def test_rapid_sprite_clicks_replace_replies_and_reach_irritation(self) -> None:
        before = self.pet.state.capture_checkpoint()
        for count in range(1, 7):
            self.click(1 if count % 2 else 3)
            self.assertEqual(len(self.pet.mind.clicks), count)
            self.assertIsNotNone(self.pet._reaction_player.pending_timer)
            self.assertTrue(self.pet._contact.can_interact("pet"))
            self.assertTrue(self.pet._contact.can_interact("play"))
        self.assertEqual(self.pet._reaction_player.event, "click_boundary")
        self.assertGreater(self.pet.mind.irritation_reaction_until, time.monotonic())
        self.assertEqual(self.pet.state.capture_checkpoint(), replace(
            before, moodlets=replace(before.moodlets, interactions=replace(
                before.moodlets.interactions,
                poke_boundary_at=self.pet.state.lived_seconds,
            )),
        ))

    def test_short_care_and_active_game_ignore_direct_clicks(self) -> None:
        self.pet.interact("pet")
        event = self.pet._reaction_player.event
        before = self.pet.state.capture_checkpoint()
        for _ in range(4):
            self.click()
            self.click(3)
        self.assertEqual(list(self.pet.mind.clicks), [])
        self.assertEqual(self.pet._reaction_player.event, event)
        self.assertEqual(self.pet.state.capture_checkpoint(), before)

        self.pet._reaction_player.cancel()
        self.pet._action_playback.cancel_at(time.monotonic())
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        self.assertTrue(self.pet._hover.game_open)
        for _ in range(4):
            self.click()
            self.click(3)
        self.assertEqual(list(self.pet.mind.clicks), [])
        self.assertTrue(self.pet._hover.game_open)

    def test_only_continued_clicks_after_boundary_cost_friendship(self) -> None:
        before = self.pet.state.friendship
        for _ in range(6):
            self.click()
        self.assertEqual(self.pet._reaction_player.event, "click_boundary")
        self.assertEqual(self.pet.state.friendship, before)
        self.click(3)
        self.assertAlmostEqual(self.pet.state.friendship, before - .25)
        for _ in range(12):
            self.click()
        # The final reply's remaining animation still blocks extra input.
        self.assertAlmostEqual(self.pet.state.friendship, before - .75)
        self.pet._action_playback.cancel_at(time.monotonic())
        for _ in range(12):
            self.click()
        self.assertAlmostEqual(self.pet.state.friendship, before - 1)
        self.assertIsNone(self.pet.state.friendship_history.last_contact)

    def test_story_reading_including_right_clicks_does_not_tease(self) -> None:
        self.pet.interact("talk")
        player = self.pet._reaction_player
        self.assertTrue(player.story_active)
        before = self.pet.state.capture_checkpoint()
        irritation = self.pet.mind.irritation_reaction_until
        for _ in range(5):
            self.click(3)
        self.assertTrue(player.story_active)
        self.assertEqual(self.pet.state.capture_checkpoint(), before)
        with patch.object(
            self.pet._care_runtime, "complete_social",
            wraps=self.pet._care_runtime.complete_social,
        ) as completed:
            for _ in range(sum(cue.kind == "text" for cue in player.cues) + 1):
                if not player.story_active:
                    break
                self.click()
            completed.assert_called_once()
        self.assertFalse(player.story_active)
        self.assertEqual(list(self.pet.mind.clicks), [])
        self.assertEqual(self.pet.mind.irritation_reaction_until, irritation)

    def test_replaced_click_reply_cannot_unlock_other_playback(self) -> None:
        self.click()
        self.assertEqual(len(self.pet.mind.clicks), 1)
        self.pet._react(Reaction.spoken("care", "Einen Moment.", "idle", "care_pet"))
        for _ in range(4):
            self.click()
        self.assertEqual(len(self.pet.mind.clicks), 1)
        self.assertEqual(self.pet._reaction_player.event, "care_pet")

    def test_sleep_clicks_request_quiet_then_wake_with_irritated_feedback(self) -> None:
        self.pet.interact("sleep")
        self.assertTrue(self.pet.state.sleeping)
        history = self.pet.state.friendship_history
        for count in range(1, 4):
            self.click(1 if count % 2 else 3)
            self.assertTrue(self.pet.state.sleeping)
            self.assertEqual(self.pet._reaction_player.event, "sleep_click")
            self.assertEqual(len(self.pet.mind.clicks), count)
            self.assertEqual(self.pet._animated.frame_clock.active_key, ("sleep", None))
            self.assertFalse(self.pet._contact.can_interact("pet"))
            self.assertTrue(self.pet._contact.can_interact("sleep"))
        self.click(3)
        self.assertFalse(self.pet.state.sleeping)
        self.assertEqual(self.pet._reaction_player.event, "click_wake")
        self.assertGreater(self.pet.mind.irritation_reaction_until, time.monotonic())
        self.assertNotEqual(self.pet._animated.frame_clock.active_key, ("sleep", None))
        self.assertEqual(self.pet.state.friendship_history, history)
        loaded = self.pet.store.load_session()
        self.assertFalse(loaded.state.sleeping)

    def test_sleep_click_pause_resets_the_burst_and_menu_wake_still_works(self) -> None:
        self.pet.interact("sleep")
        now = time.monotonic()
        for index, stamp in enumerate((now, now + 0.1, now + 8, now + 8.1)):
            with patch("aiko_pet.application.contact.time.monotonic",
                       return_value=stamp):
                self.click(1 if index % 2 else 3)
        self.assertTrue(self.pet.state.sleeping)
        self.assertEqual(len(self.pet.mind.clicks), 2)
        self.pet.interact("sleep")
        self.assertFalse(self.pet.state.sleeping)
        self.assertEqual(self.pet._reaction_player.event, "wake")

    def test_sleep_is_clickable_at_both_sprite_scales(self) -> None:
        for scale in (1, 2):
            with self.subTest(scale=scale):
                if self.pet.settings.scale != scale:
                    self.pet.toggle_scale()
                self.pet.interact("sleep")
                self.click()
                self.assertTrue(self.pet.state.sleeping)
                self.assertEqual(self.pet._reaction_player.event, "sleep_click")
                for _ in range(3):
                    self.click(3)
                self.assertFalse(self.pet.state.sleeping)
                self.assertEqual(self.pet._reaction_player.event, "click_wake")


if __name__ == "__main__":
    unittest.main()
