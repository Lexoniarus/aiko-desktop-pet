"""Isolated-save Windows/Tk acceptance of social selection and playback."""

from __future__ import annotations

import tempfile
import time
import tkinter as tk
import unittest
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from test_social_coordinator import TEST_JOKE_CATALOG, ManualSocialWorker
from test_social_sayings import quotation, quote_payload

from aiko_pet.application.social_content import SocialCategory
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_fetch import SocialFetchResult
from aiko_pet.games.contracts import GameId
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.content import GERMAN_TEXT
from aiko_pet.ui.windows.social_menu import SocialMenu
from tools.desktop_test_support import create_test_desktop
from tools.pet_test_support import set_test_pet_values


class SocialGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"No graphical display: {error}") from error
        root.destroy()

    def setUp(self) -> None:
        coordinator_patch = patch(
            "aiko_pet.desktop.care_runtime.SocialContentCoordinator",
            partial(SocialContentCoordinator, joke_catalog=TEST_JOKE_CATALOG),
        )
        coordinator_patch.start()
        self.addCleanup(coordinator_patch.stop)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.worker = ManualSocialWorker()
        clock_patch = patch("aiko_pet.application.social_coordinator.time",
                            SimpleNamespace(time=self.worker.clock))
        clock_patch.start()
        self.addCleanup(clock_patch.stop)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "state.json"),
            social_worker=self.worker,
        )
        self.addCleanup(self.pet.quit)
        self.callback_errors: list[BaseException] = []
        self.pet.root.report_callback_exception = lambda _kind, error, _trace: (
            self.callback_errors.append(error)
        )
        self.addCleanup(lambda: self.assertEqual(self.callback_errors, []))
        self.pet._runtime.stop()
        self.pet.settings.auto_routine = False
        self.pet.settings.spontaneous_talk = False
        set_test_pet_values(self.pet.state, social=10, sleeping=False)
        self.pet._reaction_player.cancel()
        self.pet._action_playback.cancel_at(time.monotonic())
        self.clock = patch(
            "aiko_pet.application.active_time.ActiveSessionClock.consume",
            return_value=0,
        )
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def menu(self) -> SocialMenu:
        self.pet._hover.show_toolbar()
        self.pet._hover._interact("talk")
        menu = self.pet._hover.social_menu
        assert menu is not None
        self.pet.root.update_idletasks()
        return menu

    def enable(self) -> None:
        self.pet._preferences.set_option("online_social", True)

    def test_menu_opens_without_effect_and_offline_plain_talk_still_works(self):
        menu = self.menu()
        self.assertEqual(len(menu.buttons), 5)
        self.assertFalse(self.worker.requests)
        self.assertEqual(self.pet.state.social, 10)
        self.assertIn(menu.frame.winfo_toplevel(), self.pet._overlay_windows())
        for category in SocialCategory:
            self.assertEqual(menu.buttons[category].cget("state"), "disabled")
        menu.choose(None)
        self.assertIsNone(self.pet._hover.social_menu)
        self.assertEqual(self.pet.state.social, 36)

    def _hide_requested_content(self, *, reply_ready: bool) -> None:
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.assertTrue(self.pet._social_runtime.waiting)
        if reply_ready:
            self.worker.complete(1)
        self.pet._hover._auto_hide_toolbar()
        self.assertIsNone(self.pet._hover.social_menu)
        self.assertTrue(self.pet._social_runtime.waiting)
        if not reply_ready:
            self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertEqual(self.pet._reaction_player.event, "talk")
        self.assertEqual(self.pet.state.social, 36)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertEqual(self.pet.state.social, 36)

    def test_automatic_hide_keeps_requested_content_until_reply(self):
        self._hide_requested_content(reply_ready=False)

    def test_reply_ready_in_hide_tick_still_starts_once(self):
        self._hide_requested_content(reply_ready=True)

    def test_browsing_game_choices_keeps_pending_social_request(self):
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.pet._hover.open_game_menu()
        self.assertTrue(self.pet._social_runtime.waiting)
        self.assertIsNotNone(self.pet._hover.game_menu)

    def test_rejected_care_or_game_does_not_cancel_pending_social(self):
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.pet.root.update()
        with patch.object(self.pet._contact, "can_interact", return_value=False):
            self.pet._hover._interact("pet")
            self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        self.assertTrue(self.pet._social_runtime.waiting)
        self.assertFalse(self.pet._hover.game_open)

    def test_accepted_game_replaces_pending_social_request(self):
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.pet._hover.open_game(GameId.ROCK_PAPER_SCISSORS)
        self.assertFalse(self.pet._social_runtime.waiting)
        self.assertTrue(self.pet._hover.game_open)
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertNotEqual(self.pet._reaction_player.event, "talk")
        self.assertEqual(self.pet.state.social, 10)

    def test_explicit_selector_close_cancels_once_and_ignores_late_reply(self):
        self.enable()
        menu = self.menu()
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        bar = self.pet._hover.toolbar
        assert bar is not None
        with patch.object(self.pet._social_runtime, "cancel",
                          wraps=self.pet._social_runtime.cancel) as cancel:
            bar.close_selector()
            menu.close()
        cancel.assert_called_once_with()
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertNotEqual(self.pet._reaction_player.event, "talk")
        self.assertEqual(self.pet.state.social, 10)

    def _request_at_phase(self, phase: str) -> None:
        self.enable()
        menu = self.menu()
        bar = self.pet._hover.toolbar
        assert bar is not None
        with (
            patch.object(self.pet.root, "winfo_pointerx",
                         return_value=bar.window.winfo_rootx() + 20),
            patch.object(self.pet.root, "winfo_pointery",
                         return_value=bar.window.winfo_rooty() + 20),
        ):
            menu.choose(SocialCategory.SINGLE)
            self.pet.root.update()
            if phase != "fetching":
                self.worker.complete(1)
                self.pet._social_runtime.poll()
            if phase == "playing":
                self.pet.root.update()
        self.assertEqual(self.pet._social_runtime._phase,
                         "idle" if phase == "playing" else phase)

    def _assert_requested_reply_once(self, phase: str) -> None:
        if phase == "fetching":
            self.worker.complete(1)
            self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertEqual(self.pet._reaction_player.event, "talk")
        self.assertEqual(self.pet.state.social, 36)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertEqual(self.pet.state.social, 36)

    def _focus_loss_preserves_request(self, phase: str) -> None:
        self._request_at_phase(phase)
        with patch.object(self.pet.root, "after",
                          return_value="focus-regression") as schedule:
            self.pet._input.on_focus_out(tk.Event())
        self.assertEqual(schedule.call_args.args[0], 100)
        callback = schedule.call_args.args[1]
        with (
            patch.object(self.pet.root, "winfo_pointerx", return_value=-999),
            patch.object(self.pet.root, "winfo_pointery", return_value=-999),
            patch.object(self.pet._social_runtime, "cancel",
                         wraps=self.pet._social_runtime.cancel) as cancel,
        ):
            callback()
        self.assertNotIn("focus-regression", self.pet._input._focus_timers)
        cancel.assert_not_called()
        self.assertIsNone(self.pet._hover.social_menu)
        self._assert_requested_reply_once(phase)

    def test_delayed_focus_loss_preserves_fetching_request(self):
        self._focus_loss_preserves_request("fetching")

    def test_delayed_focus_loss_preserves_queued_answer_start(self):
        self._focus_loss_preserves_request("admitting")

    def test_delayed_focus_loss_preserves_running_conversation(self):
        self._focus_loss_preserves_request("playing")

    def test_empty_selection_waits_without_care_then_delivers_once(self) -> None:
        self.enable()
        menu = self.menu()
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.assertTrue(self.pet._social_runtime.waiting)
        self.assertEqual(self.pet._reaction_player.event, "social_wait")
        self.assertEqual(self.pet.state.social, 10)
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertFalse(self.pet._social_runtime.waiting)
        self.assertEqual(self.pet._reaction_player.event, "talk")
        self.assertEqual(self.pet.state.social, 36)
        self.assertEqual(self.pet._reaction_player.cues[-1].content, "Test 1.")
        self.pet._social_runtime.poll()
        self.pet._reaction_player.advance_story()
        self.assertEqual(self.pet.state.social, 36)
        menu.refresh()
        self.pet._hover.open_settings(100, 100)
        settings = self.pet._hover.settings_window
        assert settings is not None
        settings.select_section("credits")
        self.assertEqual(settings.credits.source_button.cget("text"), "Quelle: JokeAPI")

    def test_ready_content_starts_without_waiting_and_excludes_other_care(self):
        self.enable()
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        menu = self.menu()
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.assertEqual(self.pet.state.social, 36)
        self.assertEqual(self.pet._reaction_player.event, "talk")
        self.assertFalse(self.pet._contact.can_interact("pet"))
        self.assertIsNotNone(self.pet._reaction_player.pending_timer)

    def test_quote_uses_same_saying_choice_care_and_native_credits(self):
        self.enable()
        menu = self.menu()
        self.assertEqual(menu.buttons[SocialCategory.SINGLE].cget("text"), "Sprüche")
        self.assertEqual(len(menu.buttons), 5)
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.worker.complete(1, fail=True)
        self.pet._social_runtime.poll()
        category, token = self.worker.requests[-1]
        item = quotation(quote_payload())
        self.worker.result = SocialFetchResult(token, category, item)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertEqual(self.pet.state.social, 36)
        cues = self.pet._reaction_player.cues
        texts = [cue for cue in cues if cue.kind == "text"]
        self.assertEqual(texts[1].content, quote_payload()["quote"])
        self.assertEqual(texts[2].content, "Von René Descartes.")
        self.assertEqual(texts[2].duration_ms, 5000)
        self.assertEqual(len(self.pet._social_runtime.content.history.entries), 1)
        self.pet._hover.open_settings(100, 100)
        settings = self.pet._hover.settings_window
        assert settings is not None
        settings.select_section("credits")
        self.pet.root.update_idletasks()
        self.assertIn("René Descartes", settings.credits.accepted.cget("text"))
        self.assertIn("CC BY 4.0", settings.credits.accepted.cget("text"))
        self.assertEqual(settings.credits.author_button.cget("state"), "normal")
        with patch("aiko_pet.ui.windows.credits_panel.webbrowser.open") as opened:
            settings.credits._open_author()
            settings.credits._open_source()
            settings.credits._open_entry()
        self.assertEqual([call.args[0] for call in opened.call_args_list], [
            item.author_url, item.source_url, item.permalink,
        ])
        self.pet._social_runtime.poll()
        self.assertEqual(self.pet.state.social, 36)

    def test_other_care_cancels_holding_and_late_reply_cannot_start(self) -> None:
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.assertTrue(self.pet._contact.can_interact("pet"))
        self.pet._hover._interact("pet")
        self.assertFalse(self.pet._social_runtime.waiting)
        self.assertIsNone(self.pet._hover.social_menu)
        after_care = self.pet.state.social
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        self.assertEqual(self.pet.state.social, after_care)
        self.assertNotEqual(self.pet._reaction_player.event, "talk")

    def test_error_dismiss_disable_and_shutdown_never_award_waiting(self) -> None:
        self.enable()
        menu = self.menu()
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.worker.complete(1, fail=True)
        self.pet._social_runtime.poll()
        self.worker.complete(2, fail=True)
        self.pet._social_runtime.poll()
        menu.refresh()
        self.assertIn("erneuten", menu.status.cget("text"))
        self.assertEqual(self.pet.state.social, 10)
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.pet._hover.dismiss_outside(-999, -999)
        self.assertFalse(self.pet._social_runtime.waiting)
        self.assertIsNone(self.pet._hover.social_menu)
        self.pet._preferences.set_option("online_social", False)
        self.assertEqual(self.pet.state.social, 10)
        self.pet.quit()
        self.assertTrue(self.worker.closed)

    def test_fact_introduction_and_two_part_pause_survive_real_player(self) -> None:
        self.enable()
        for identifier in range(3):
            self.worker.complete(identifier)
            self.pet._social_runtime.poll()
        menu = self.menu()
        menu.choose(SocialCategory.TWO_PARTS)
        self.pet.root.update()
        cues = self.pet._reaction_player.cues
        self.assertIn(cues[0].content, tuple(
            GERMAN_TEXT.format(f"social.intro.twopart{suffix}")
            for suffix in ("", "_alt1", "_alt2")
        ))
        self.assertEqual(cues[1].content, "Test 1.")
        self.assertEqual(cues[2].kind, "pause")
        self.assertEqual(cues[2].duration_ms, 800)
        self.assertEqual(cues[3].content, "Eine Testantwort.")
        self.pet._reaction_player.cancel()
        menu.choose(SocialCategory.FACT)
        self.pet.root.update()
        self.assertIn(
            self.pet._reaction_player.cues[0].content,
            tuple(GERMAN_TEXT.format(f"social.intro.fact{suffix}")
                  for suffix in ("", "_alt1", "_alt2")),
        )
        self.assertEqual(self.pet._reaction_player.cues[1].content, "Test 2.")
        self.assertEqual(self.pet.state.social, 62)

    def test_menu_stays_bounded_and_escape_cancels_only_pending_content(self):
        self.enable()
        width = self.pet.root.winfo_screenwidth()
        height = self.pet.root.winfo_screenheight()
        self.pet._save_hover_position(width - 50, height - 70)
        menu = self.menu()
        menu.choose(SocialCategory.SINGLE)
        self.pet.root.update()
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        menu.refresh()
        self.pet.root.update_idletasks()
        self.assertGreaterEqual(menu.frame.winfo_toplevel().winfo_x(), 0)
        self.assertGreaterEqual(menu.frame.winfo_toplevel().winfo_y(), 0)
        self.assertLessEqual(
            menu.frame.winfo_toplevel().winfo_x()
            + menu.frame.winfo_toplevel().winfo_width(),
            width,
        )
        self.assertLessEqual(
            menu.frame.winfo_toplevel().winfo_y()
            + menu.frame.winfo_toplevel().winfo_height(),
            height,
        )
        menu.frame.winfo_toplevel().focus_force()
        menu.frame.winfo_toplevel().event_generate("<Escape>")
        self.pet.root.update()
        self.assertIsNone(self.pet._hover.social_menu)
        self.assertEqual(self.pet._reaction_player.event, "talk")
        self.assertEqual(self.pet.state.social, 36)

    def test_save_reopen_keeps_opt_in_and_shared_rewards_without_content_cache(self):
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.worker.complete(1)
        self.pet._social_runtime.poll()
        self.pet.root.update()
        friendship = self.pet.state.friendship
        store = self.pet.store
        self.pet.quit()
        saved = store.load_session()
        self.assertTrue(saved.settings.online_social)
        self.assertEqual(len(saved.social_history.entries), 1)
        receipt = saved.social_history.entries[0]
        self.assertEqual(receipt.category, SocialCategory.SINGLE)
        self.assertEqual(receipt.identity, "jokeapi:1")
        self.assertEqual(len(receipt.fingerprint), 64)
        worker = ManualSocialWorker(clock=self.worker.clock)
        reopened = create_test_desktop(store=store, social_worker=worker)
        reopened.root.report_callback_exception = lambda _kind, error, _trace: (
            self.callback_errors.append(error)
        )
        self.addCleanup(reopened.quit)
        reopened._runtime.stop()
        self.assertTrue(reopened.settings.online_social)
        self.assertEqual(len(worker.requests), 1)
        self.assertTrue(
            all(reopened._social_runtime.content.count(c) == 0 for c in SocialCategory)
        )
        reopened._reaction_player.cancel()
        reopened._action_playback.cancel_at(time.monotonic())
        reopened._social_runtime.select(SocialCategory.FACT)
        worker.complete(2)
        reopened._social_runtime.poll()
        worker.complete(3)
        reopened._social_runtime.poll()
        reopened.root.update()
        self.assertEqual(reopened._reaction_player.event, "talk")
        self.assertAlmostEqual(reopened.state.friendship, friendship, places=4)

    def test_expired_holding_bubble_still_blocks_sprite_replies_but_allows_care(self):
        self.enable()
        self.menu().choose(SocialCategory.SINGLE)
        self.pet.root.update()
        player = self.pet._reaction_player
        assert player.pending_timer is not None
        self.pet.root.after_cancel(player.pending_timer)
        player._complete(player.generation)
        self.assertTrue(self.pet._social_runtime.waiting)
        self.assertIsNone(player.event)
        before = list(self.pet.mind.clicks)
        self.pet._contact.click("left")
        self.pet._contact.enter()
        self.assertEqual(list(self.pet.mind.clicks), before)
        self.assertIsNone(player.event)
        self.assertTrue(self.pet._contact.can_interact("pet"))
        self.pet._hover._interact("pet")
        self.assertFalse(self.pet._social_runtime.waiting)
