"""Real wish command/persistence path with headless widget callbacks."""

import unittest
from typing import Any, cast
from unittest.mock import Mock

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.controller import CareController
from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.desktop.care_runtime import DesktopCareRuntime
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.common.description_tip import DescriptionTip
from aiko_pet.ui.view_models.emotional_text import wish_description
from aiko_pet.ui.view_models.projections import project_hover
from aiko_pet.ui.windows.wish_panel import WishPanel
from tools.headless_widgets import Skin, Widget, widgets


class WishControlTests(unittest.TestCase):
    def test_pin_and_right_click_use_existing_commands_and_persist_neutrally(self):
        wall = 1800000000
        pet = PetState(
            updated_at=wall,
            wishes=WishState(2, (ActiveWish(1, WishId.FACT, "fact", 0, 14400),),
                             ((WishArea.SOCIAL, 0),)),
            moodlets=MoodletState(next_instance_id=2, active=(
                MoodletEpisode(1, MoodletId.CHEERFUL, 1, 0, 0, 7200),
            )),
        )
        initial_moodlets, relationship = pet.moodlets, pet.friendship_history
        router = ApplicationRouter(CareController(
            pet, make_aiko_mind(started_at=0), AdaptiveRoutine(),
            clock=ActiveSessionClock(lambda: 0),
        ))
        runtime = DesktopCareRuntime.__new__(DesktopCareRuntime)
        runtime._router = router
        runtime._inputs = lambda _wall, _now: SessionInputs(
            wall, 0, False, None, False, False, None,
        )
        saved: list[dict[str, Any]] = []
        runtime._save = lambda: saved.append(encode_pet_state(pet))
        runtime._hover = cast(Any, Mock())

        def views():
            return project_hover(snapshot_pet(pet), context_at(wall),
                                 ComputerSnapshot(), observe_computer=False
                                 ).emotional.wishes

        with widgets():
            skin, root = Skin(), Widget()
            panel = WishPanel(cast(Any, root), cast(Any, skin),
                              DescriptionTip(cast(Any, root), cast(Any, skin)), {},
                              pin_wish=runtime.set_wish_pinned,
                              dismiss_wish=runtime.dismiss_wish)
            panel.refresh(views())
            cards = panel._scroll.body.winfo_children()
            panel._pins[1].invoke()
            self.assertTrue(pet.wishes.active[0].pinned)
            panel.refresh(views())
            self.assertEqual(panel._scroll.body.winfo_children(), cards)
            self.assertTrue(panel._pins[1].cget("selected"))
            self.assertIn("ohne Zeitablauf", panel._meta[1].cget("text"))
            self.assertNotIn("Noch", wish_description(views()[0]))
            panel._pins[1].invoke()
            self.assertFalse(pet.wishes.active[0].pinned)
            # Right click any card content; remove the real wish, not its Moodlet.
            cast(Widget, cast(Any, panel._labels[1])).bindings["<Button-3>"](Mock())
            panel.refresh(views())
            self.assertFalse(pet.wishes.active)
            self.assertEqual(pet.wishes.refill_not_before, 720)
            self.assertEqual(pet.moodlets, initial_moodlets)
            self.assertEqual(pet.friendship_history, relationship)
            self.assertEqual(len(saved), 3)
            loaded = decode_pet_state(saved[-1], now=wall)
            self.assertEqual(loaded.wishes, pet.wishes)
            self.assertEqual(loaded.moodlets, pet.moodlets)
            first = decode_pet_state(saved[0], now=wall)
            self.assertTrue(first.wishes.active[0].pinned)
            self.assertEqual(runtime._hover.refresh_toolbar.call_count, 3)
            # A queued callback for a retired card is harmless.
            panel._dismiss(1, cast(Any, Mock()))
            self.assertEqual(len(saved), 3)
