"""Native isolated-save admission and playback of the reviewed library source."""

import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from support.social import ManualSocialWorker

from aiko_pet.application.social_content import SocialCategory, SocialProvider
from aiko_pet.infrastructure.local_jokes import load_local_jokes
from aiko_pet.infrastructure.persistence import StateStore
from tools.desktop_test_support import create_test_desktop
from tools.pet_test_support import set_test_pet_values
from tools.tk_test_time import ControlledTkTime


class LocalJokeGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
        except tk.TclError as error:
            raise unittest.SkipTest(f"No graphical display: {error}") from error
        root.destroy()

    def test_local_joke_plays_and_saves_care_once_without_a_network_response(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            ControlledTkTime() as clock,
            patch("aiko_pet.application.active_time.ActiveSessionClock.consume",
                  return_value=0),
        ):
            store = StateStore(Path(directory) / "local-joke.sqlite3")
            worker = ManualSocialWorker()
            pet = create_test_desktop(
                store=store, social_worker=worker,
                local_social_content=load_local_jokes(),
            )
            try:
                pet._runtime.stop()
                pet.settings.auto_routine = False
                pet.settings.spontaneous_talk = False
                set_test_pet_values(pet.state, social=10, sleeping=False)
                pet._reaction_player.cancel()
                pet._action_playback.cancel_at(clock.monotonic())
                pet._preferences.set_option("online_social", True)
                pet._care_runtime.select_social(SocialCategory.TWO_PARTS)
                clock.advance(1)
                _status, content = pet._social_runtime.snapshot()
                assert content is not None
                self.assertEqual(content.provider, SocialProvider.PYJOKES)
                self.assertEqual(pet._reaction_player.event, "talk")
                self.assertEqual(pet.state.social, 36)
                self.assertEqual(len(pet._social_runtime.content.history.entries), 1)
                self.assertIsNone(worker.result)  # No HTTP result was ever provided.
                saved = store.load_session(now=clock.wall_time())
                self.assertEqual(saved.social_history.entries[0].identity,
                                 content.identity)
                duration = sum(beat.duration_ms for beat in content.reaction.beats)
                clock.advance((duration + 2000) / 1000)
                self.assertEqual(pet.state.social, 36)
            finally:
                pet.quit()
