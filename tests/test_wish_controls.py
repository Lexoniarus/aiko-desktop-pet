"""Real wish command/persistence path with headless widget callbacks."""

import unittest
from typing import Any, cast
from unittest.mock import Mock, patch

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.controller import CareController
from aiko_pet.application.read_snapshot import snapshot_pet
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.desktop.care_runtime import DesktopCareRuntime
from aiko_pet.frontend.view_models.emotional_text import wish_description
from aiko_pet.frontend.view_models.projections import project_hover
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.moodlets import MoodletEpisode, MoodletId, MoodletState
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.common.description_tip import DescriptionTip
from aiko_pet.ui.windows.wish_panel import WishPanel
from tools.headless_widgets import Skin, Widget, widgets


class WishControlTests(unittest.TestCase):
    def setUp(self):
        wall = 1800000000
        pet = PetState(
            updated_at=wall,
            wishes=WishState(
                2,
                (ActiveWish(1, WishId.FACT, "fact", 0, 14400),),
                ((WishArea.SOCIAL, 0),),
            ),
            moodlets=MoodletState(
                next_instance_id=2,
                active=(MoodletEpisode(1, MoodletId.CHEERFUL, 1, 0, 0, 7200),),
            ),
        )
        router = ApplicationRouter(
            CareController(
                pet,
                make_aiko_mind(started_at=0),
                AdaptiveRoutine(),
                clock=ActiveSessionClock(lambda: 0),
            )
        )
        runtime = DesktopCareRuntime.__new__(DesktopCareRuntime)
        runtime._router = router
        runtime._inputs = lambda _wall, _now: SessionInputs(
            wall,
            0,
            False,
            None,
            False,
            False,
            None,
        )
        saved: list[dict[str, Any]] = []
        runtime._save = lambda: saved.append(encode_pet_state(pet))
        runtime._hover = cast(Any, Mock())

        def views():
            return project_hover(
                snapshot_pet(pet),
                context_at(wall),
                ComputerSnapshot(),
                observe_computer=False,
            ).emotional.wishes

        self.pet, self.runtime, self.saved, self.views = pet, runtime, saved, views
        self.enterContext(widgets())
        skin, root = Skin(), Widget()
        self.panel = WishPanel(
            cast(Any, root),
            cast(Any, skin),
            DescriptionTip(cast(Any, root), cast(Any, skin)),
            {},
            pin_wish=runtime.set_wish_pinned,
            dismiss_wish=runtime.dismiss_wish,
        )
        self.panel.refresh(views())

    def test_pin_serializes_once_and_refreshes_existing_card(self):
        panel, pet = self.panel, self.pet
        cards = panel._content.body.winfo_children()
        label = cast(Any, panel._labels[1])
        self.assertEqual(label.bindings["<Button-1>"](Mock()), "break")
        self.assertTrue(pet.wishes.active[0].pinned)
        with patch.object(panel._pin_icons[1], "itemconfigure") as marker:
            panel.refresh(self.views())
            marker.assert_called_once_with("pin", state="normal")
        self.assertEqual(panel._content.body.winfo_children(), cards)
        self.assertIn("ohne Zeitablauf", panel._meta[1].cget("text"))
        self.assertNotIn("Noch", wish_description(self.views()[0]))
        label.bindings["<Button-1>"](Mock())
        self.assertEqual(len(self.saved), 1)
        self.assertTrue(
            decode_pet_state(self.saved[0], now=1800000000).wishes.active[0].pinned
        )
        self.assertEqual(cast(Mock, self.runtime._hover.refresh_toolbar).call_count, 1)

    def test_first_right_click_unpins_and_preserves_identity(self):
        self.runtime.set_wish_pinned(1, True)
        self.panel.refresh(self.views())
        self.saved.clear()
        before = self.pet.wishes.active[0]
        cast(Any, self.panel._pin_icons[1]).bindings["<Button-3>"](Mock())
        self.assertEqual(len(self.pet.wishes.active), 1)
        wish = self.pet.wishes.active[0]
        self.assertFalse(wish.pinned)
        self.assertEqual(wish.instance_id, before.instance_id)
        self.assertEqual(wish.expires_at, 600)
        with patch.object(self.panel._pin_icons[1], "itemconfigure") as marker:
            self.panel.refresh(self.views())
            marker.assert_called_once_with("pin", state="hidden")
        self.assertEqual(len(self.saved), 1)
        self.assertFalse(
            decode_pet_state(self.saved[0], now=1800000000).wishes.active[0].pinned
        )

    def test_dismissal_serializes_without_care_and_stale_callbacks_are_harmless(self):
        before = self.pet.capture_checkpoint()
        cast(Any, self.panel._labels[1]).bindings["<Button-3>"](Mock())
        self.panel.refresh(self.views())
        self.assertFalse(self.pet.wishes.active)
        self.assertEqual(self.pet.wishes.refresh_at, 600)
        self.assertEqual(self.pet.moodlets, before.moodlets)
        self.assertEqual(self.pet.friendship_history, before.relationship)
        self.assertEqual(len(self.saved), 1)
        loaded = decode_pet_state(self.saved[0], now=1800000000)
        self.assertEqual(loaded.wishes, self.pet.wishes)
        self.assertEqual(loaded.moodlets, self.pet.moodlets)
        self.panel._unpin_or_dismiss(1, cast(Any, Mock()))
        self.panel._pin(1, cast(Any, Mock()))
        self.assertEqual(len(self.saved), 1)
        self.assertEqual(cast(Mock, self.runtime._hover.refresh_toolbar).call_count, 1)

    def test_all_card_surfaces_share_controls_without_constructing_a_button(self):
        pet = PetState(wishes=WishState(active=(
            ActiveWish(1, WishId.FACT, "fact", 0, 14400),
        )))
        view = project_hover(snapshot_pet(pet), context_at(1800000000),
                             ComputerSnapshot(), observe_computer=False)
        with widgets():
            skin, root = Skin(), Widget()
            surface_factory = skin.surface

            def surface(parent):
                result = surface_factory(parent)
                Widget(result.frame)  # Passive artwork behind the body/padding.
                return result

            with (
                patch.object(skin, "surface", surface),
                patch.object(skin, "button", side_effect=AssertionError("No button")),
            ):
                pin, dismiss = Mock(), Mock()
                panel = WishPanel(cast(Any, root), cast(Any, skin),
                                  DescriptionTip(cast(Any, root), cast(Any, skin)), {},
                                  pin_wish=pin, dismiss_wish=dismiss)
                panel.refresh(view.emotional.wishes)

            def check(widget):
                pin.reset_mock()
                dismiss.reset_mock()
                self.assertEqual(widget.bindings["<Button-1>"](Mock()), "break")
                pin.assert_called_once_with(1, True)
                dismiss.assert_not_called()
                self.assertEqual(widget.bindings["<Button-3>"](Mock()), "break")
                dismiss.assert_called_once_with(1)
                for child in widget.winfo_children():
                    check(child)

            check(panel._cards[0].frame)
