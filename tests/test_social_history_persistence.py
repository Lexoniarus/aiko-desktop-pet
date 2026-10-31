"""Actual local saves and playback admission without windows or live APIs."""

import hashlib
import tempfile
import tkinter as tk
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from test_social_coordinator import TEST_JOKE_CATALOG, ManualSocialWorker

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.controller import CareController
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.application.session import PetSessionRestorer
from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_content import BUFFERED_CATEGORIES, SocialCategory
from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.application.social_history import (
    SocialContentHistory,
    SocialContentReceipt,
)
from aiko_pet.desktop.care_runtime import DesktopCareRuntime
from aiko_pet.desktop.persistence import DesktopPersistence
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from tools.persistence_test_support import save_test_session
from tools.reaction_test_support import FakeScheduler


class SocialHistoryPersistenceTests(unittest.TestCase):
    def setUp(self):
        coordinator_patch = patch(
            "aiko_pet.desktop.care_runtime.SocialContentCoordinator",
            partial(SocialContentCoordinator, joke_catalog=TEST_JOKE_CATALOG),
        )
        coordinator_patch.start()
        self.addCleanup(coordinator_patch.stop)
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.store = StateStore(Path(folder.name) / "state.json")
        self.wall = 1800000000
        self.pet = PetState(
            updated_at=self.wall,
            social=20,
            wishes=WishState(
                2,
                (ActiveWish(1, WishId.SINGLE, "single", 0, 14400),),
                ((WishArea.SOCIAL, 0),),
            ),
        )
        self.settings = PetSettings(auto_routine=False)

    def test_old_saves_have_empty_history_without_changing_pet_values(self):
        save_test_session(self.store, self.pet, self.settings)
        before = self.pet.capture_checkpoint()
        loaded = self.store.load_session(now=self.wall)
        self.assertEqual(loaded.social_history, SocialContentHistory())
        self.assertEqual(loaded.state.capture_checkpoint(), before)
        restored = PetSessionRestorer(self.store, wall_time=lambda: self.wall).restore()
        self.assertEqual(restored.social_history, SocialContentHistory())
        self.assertEqual(restored.state.social, 20)

    def test_restore_prevents_first_repeat_after_restart(self):
        history = SocialContentHistory((SocialContentReceipt(
            SocialCategory.SINGLE, "jokeapi:1", hashlib.sha256(b"test 1.").hexdigest(),
        ),))
        persistence = DesktopPersistence(
            self.store, self.pet, self.settings, AdaptiveRoutine(),
            social_history=lambda: history,
        )
        self.assertIsNone(persistence.save())
        self.assertEqual(self.store.load_session().social_history, history)
        restored = PetSessionRestorer(self.store, wall_time=lambda: self.wall).restore()
        self.assertEqual(restored.social_history, history)
        worker = ManualSocialWorker()
        content = SocialContentCoordinator(
            worker,
            joke_catalog=TEST_JOKE_CATALOG,
            history=restored.social_history,
            wall_time=worker.clock,
        )
        content.set_enabled(True)
        content.select(SocialCategory.SINGLE)
        for _ in range(2):
            worker.complete(1)  # Same ID, changed body still cannot repeat.
            self.assertIsNone(content.poll())
        worker.complete(2)
        result = content.poll()
        assert result is not None and result.content is not None
        self.assertEqual(result.status, "ready")
        self.assertEqual(content.history.entries, history.entries)
        content.accept(result.content)
        self.assertEqual(len(content.history.entries), 2)

    def test_intro_rotation_survives_restarts_and_preserves_provider_body(self):
        history = SocialContentHistory(tuple(
            SocialContentReceipt(category, identity, digit * 64)
            for category, identity, digit in (
                (SocialCategory.SINGLE, "jokeapi:999", "a"),
                (SocialCategory.TWO_PARTS, "jokeapi:998", "b"),
                (SocialCategory.FACT, "uselessfacts:legacy", "c"),
            )
        ))  # Old receipts have no framing metadata; retain their known hash variant.
        save_test_session(self.store, self.pet, self.settings, social_history=history)
        identifier, originals = 10000, {}
        for session in range(3):
            restored = PetSessionRestorer(
                self.store, wall_time=lambda: self.wall,
            ).restore()
            worker = ManualSocialWorker()
            worker.clock.now += session * 3600
            content = SocialContentCoordinator(
                worker, joke_catalog=TEST_JOKE_CATALOG,
                history=restored.social_history, wall_time=worker.clock,
            )
            content.set_enabled(True)
            persistence = DesktopPersistence(
                self.store, restored.state, restored.settings, restored.adaptive,
                revision=restored.revision, social_history=lambda: content.history,
            )

            def select(category):
                nonlocal identifier
                selection = content.select(category)
                for _ in range(12):
                    if selection is not None and selection.status == "ready":
                        assert selection.content is not None
                        return selection.content
                    identifier += 1
                    worker.complete(identifier)
                    assert worker.result is not None
                    assert worker.result.content is not None
                    original = worker.result.content
                    originals[original.identity] = original
                    selection = content.poll()
                self.fail("Expected bounded fake-worker preparation to finish")

            for category in BUFFERED_CATEGORIES:
                last = next(e for e in reversed(content.history.entries)
                            if e.category == category)
                previous = (last.intro_variant if last.intro_variant is not None
                            else int(last.fingerprint[:2], 16) % 3)
                before = content.history.entries
                item = select(category)
                if session == 0 and category == SocialCategory.SINGLE:
                    content.cancel_selection()
                    self.assertEqual(content.history.entries, before)
                    item = select(category)
                self.assertEqual(item.intro_variant, (previous + 1) % 3)
                self.assertEqual(content.history.entries, before)
                original = originals[item.identity]
                self.assertEqual(item.fingerprint, original.fingerprint)
                self.assertEqual(item.reaction.beats[1:], original.reaction.beats[1:])
                scheduler, texts = FakeScheduler(), []
                player = ReactionPlayer(
                    schedule=scheduler.schedule, cancel_timer=scheduler.cancel,
                    display_text=lambda text, _ms: texts.append(text),
                    display_emote=Mock(), start_action=Mock(), mark_spoken=Mock(),
                    is_closed=lambda: False,
                )
                content.accept(item)
                self.assertIsNone(persistence.save())
                player.play(item.reaction)
                while player.pending_timer is not None:
                    scheduler.fire(player.pending_timer)
                self.assertEqual(texts, [b.content for b in item.reaction.beats
                                         if b.kind == "text"])
                self.assertEqual(self.store.load_session().social_history,
                                 content.history)
            content.close()

    def test_admission_saves_care_and_receipt_once_before_full_wish_completion(self):
        adaptive = AdaptiveRoutine()
        router = ApplicationRouter(
            CareController(
                self.pet,
                make_aiko_mind(started_at=0),
                adaptive,
                clock=ActiveSessionClock(lambda: 0),
            )
        )
        scheduler, deferred, worker = FakeScheduler(), [], ManualSocialWorker()
        root = MagicMock(spec=tk.Tk)
        root.after.side_effect = lambda _delay, callback: deferred.append(callback)
        world, contact = Mock(), Mock()
        world.cursor.carrying, world.interaction.active = False, False
        world.awareness.intentions.goal = None
        world.interrupt.side_effect = lambda callback: callback()
        world.arrangement_ready.return_value = False
        contact.can_interact.return_value = True
        player = ReactionPlayer(
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            display_text=Mock(),
            display_emote=Mock(),
            start_action=Mock(),
            mark_spoken=Mock(),
            is_closed=lambda: False,
            social_completed=lambda completion: runtime.complete_social(completion),
        )
        persistence = DesktopPersistence(
            self.store,
            self.pet,
            self.settings,
            adaptive,
            social_history=lambda: runtime.social.content.history,
        )
        runtime = DesktopCareRuntime(
            root=root,
            state=self.pet,
            router=router,
            world=world,
            contact=contact,
            animated=Mock(),
            player=player,
            speech=Mock(),
            hover=Mock(),
            cancel_action=Mock(),
            start_action=Mock(),
            react=lambda reaction, duration: player.play(reaction, duration),
            inputs=lambda _wall, _now: SessionInputs(
                self.wall,
                0,
                False,
                None,
                False,
                False,
                None,
            ),
            set_context=Mock(),
            save=lambda: self.assertIsNone(persistence.save()),
            is_closed=lambda: False,
            game_open=lambda: False,
            social_worker=worker,
            mind=make_aiko_mind(started_at=0),
        )
        runtime.social.set_enabled(True)
        worker.complete(1)
        runtime.social.poll()
        with patch.object(self.store, "save", wraps=self.store.save) as saved:
            runtime.social.select(SocialCategory.SINGLE)
            cancelled = deferred.pop()
            runtime.social.cancel()
            cancelled()
            self.assertFalse(runtime.social.content.history.entries)
            saved.assert_not_called()
            self.assertEqual(self.pet.social, 20)
            for identifier in range(2, 5):
                worker.complete(identifier)
                runtime.social.poll()
                if runtime.social.content.count(SocialCategory.SINGLE):
                    break
            runtime.social.select(SocialCategory.SINGLE)
            deferred.pop()()
            self.assertEqual(self.pet.social, 46)
            self.assertTrue(self.pet.wishes.active)
            self.assertFalse(self.pet.moodlets.active)
            self.assertEqual(saved.call_count, 1)
            loaded = self.store.load_session(now=self.wall)
            self.assertEqual(loaded.state.social, 46)
            self.assertEqual(loaded.social_history, runtime.social.content.history)
            self.assertEqual(len(loaded.social_history.entries), 1)
            history = loaded.social_history
            while player.pending_timer is not None:
                scheduler.fire(player.pending_timer)
            self.assertFalse(self.pet.wishes.active)
            self.assertTrue(self.pet.moodlets.active)
            self.assertEqual(runtime.social.content.history, history)
            # One admission save, then one real full-sequence completion save.
            self.assertEqual(saved.call_count, 2)
