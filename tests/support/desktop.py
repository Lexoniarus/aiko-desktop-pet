from __future__ import annotations

import tempfile
import time
from functools import partial
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from aiko_pet.application.social_coordinator import SocialContentCoordinator
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.ui.windows.social_menu import SocialMenu
from support.social import (
    TEST_JOKE_CATALOG,
    ManualSocialWorker,
)
from tools.desktop_test_support import create_test_desktop, require_tk_display
from tools.pet_test_support import set_test_pet_values


class SocialDesktopFixture:
    @classmethod
    def setUpClass(cls) -> None:
        require_tk_display()

    def prepare_fixture(self, cleanup) -> None:
        coordinator_patch = patch(
            "aiko_pet.desktop.care_runtime.SocialContentCoordinator",
            partial(SocialContentCoordinator, joke_catalog=TEST_JOKE_CATALOG),
        )
        coordinator_patch.start()
        cleanup(coordinator_patch.stop)
        folder = tempfile.TemporaryDirectory()
        cleanup(folder.cleanup)
        self.worker = ManualSocialWorker()
        clock_patch = patch(
            "aiko_pet.application.social_coordinator.time",
            SimpleNamespace(time=self.worker.clock),
        )
        clock_patch.start()
        cleanup(clock_patch.stop)
        self.pet = create_test_desktop(
            store=StateStore(Path(folder.name) / "state.json"),
            social_worker=self.worker,
        )
        cleanup(self.pet.quit)
        self.callback_errors: list[BaseException] = []
        self.pet.root.report_callback_exception = (
            lambda _kind, error, _trace: self.callback_errors.append(error)
        )
        cleanup(lambda: self.check_callbacks())
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
        cleanup(self.clock.stop)

    def menu(self) -> SocialMenu:
        self.pet._hover.show_toolbar()
        self.pet._hover._interact("talk")
        menu = self.pet._hover.social_menu
        assert menu is not None
        self.pet.root.update_idletasks()
        return menu

    def check_callbacks(self):
        if self.callback_errors:
            raise AssertionError(self.callback_errors)
