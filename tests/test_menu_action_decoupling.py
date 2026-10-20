"""Menu admission and finite snack placement without Tk or native input."""

import tkinter as tk
import unittest
from typing import cast
from unittest.mock import MagicMock, patch

from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.cursor_item_gesture import CursorItemGesture, CursorItemPorts
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime
from aiko_pet.pet.animation.item_assets import ItemCatalog
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.state import PetState
from aiko_pet.ui.pet_view.object_feedback_presenter import ObjectFeedbackPresenter
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.hover_contracts import HoverActions
from aiko_pet.ui.windows.hover_ui import HoverUi, HoverUiPorts
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectInteraction,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.reaction_test_support import FakeScheduler


class MenuAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.ui = HoverUi.__new__(HoverUi)
        self.ui.root = MagicMock(spec=tk.Tk)
        self.ui._skin = MagicMock()
        self.ui_ports = MagicMock(spec=HoverUiPorts)
        self.ui._ports = self.ui_ports
        self.ui_ports.can_interact.return_value = False
        self.ui_ports.can_place_item.return_value = True
        self.ui.toolbar = None
        self.ui.food_menu = None
        self.ui.game_menu = None
        self.ui.social_menu = None
        self.ui.game_window = MagicMock()
        self.ui._pending_game = None

    def test_snack_selector_and_choice_work_while_character_actions_are_blocked(self):
        with patch("aiko_pet.ui.windows.hover_ui.FoodMenu") as menu:
            self.ui._interact("place_item")
            self.ui.open_food_menu()
            menu.assert_called_once()
            menu.return_value.focus.assert_called_once()
        self.ui._food_selected("apple")
        self.ui_ports.place_item.assert_called_once_with("apple")
        self.ui._interact("pet")
        self.ui_ports.care.assert_not_called()
        self.ui_ports.can_interact.assert_called_once_with("pet")

    def test_choice_rechecks_capture_admission_after_selector_was_opened(self):
        with patch("aiko_pet.ui.windows.hover_ui.FoodMenu") as menu:
            self.ui.open_food_menu()
            self.ui_ports.can_place_item.return_value = False
            self.ui._food_selected("apple")
            self.ui.open_food_menu()
            menu.assert_called_once()
        self.ui_ports.place_item.assert_not_called()

    def test_toolbar_displays_separate_placement_and_care_capabilities(self):
        toolbar = ActionToolbar.__new__(ActionToolbar)
        toolbar._actions = MagicMock(spec=HoverActions)
        toolbar._actions.can_interact.return_value = False
        toolbar._actions.can_place_item.return_value = True
        buttons = {action: MagicMock() for action in ("place_item", "pet")}
        toolbar.buttons = cast(dict[str, tk.Button], buttons)
        toolbar.refresh_actions()
        buttons["place_item"].configure.assert_called_once_with(state="normal")
        buttons["pet"].configure.assert_called_once_with(state="disabled")
        toolbar._actions.can_interact.assert_called_once_with("pet")


class SnackPlacementTests(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock(spec=tk.Tk)
        self.root.tk = MagicMock()
        self.root.tk.call.return_value = ""
        self.root.grab_set.side_effect = lambda: setattr(
            self.root.tk.call, "return_value", str(self.root),
        )
        self.root.grab_release.side_effect = lambda: setattr(
            self.root.tk.call, "return_value", "",
        )
        self.world = WorldState(WorldSurface(800, 600), (ObjectDefinition(
            "apple", "apple", "apple", frozenset((ObjectInteraction.EAT,)),
        ),))
        self.ports = MagicMock(spec=CursorItemPorts)
        self.ports.handover.return_value = False
        self.cursor = CursorItemGesture(
            root=self.root, world=self.world, view=MagicMock(),
            settings=PetSettings(), track=MagicMock(), ports=self.ports,
        )
        self.cursor.view.image = MagicMock()
        self.cursor.view.image.return_value.width.return_value = 16
        self.enterContext(patch.object(
            self.cursor, "_pointer_pose", return_value=(WorldPosition(100, 0), True),
        ))
        self.runtime = DesktopWorldRuntime.__new__(DesktopWorldRuntime)
        self.runtime._closed = False
        self.runtime.cursor = self.cursor
        self.runtime.state = PetState()
        self.behavior = MagicMock()
        self.runtime._behavior = self.behavior
        self.awareness = MagicMock()
        self.runtime.awareness = self.awareness
        self.walk = MagicMock()
        self.runtime._walk = self.walk
        self.runtime._visual = MagicMock()
        self.interaction = MagicMock()
        self.runtime.interaction = self.interaction
        self.runtime._game_open = MagicMock(return_value=True)
        self.runtime._character_action_busy = MagicMock(return_value=True)
        self.enterContext(patch.object(self.runtime, "_sync_geometry"))

    def test_busy_action_or_sleep_does_not_block_stock_or_interrupt_aiko(self):
        for sleeping in (False, True):
            with self.subTest(sleeping=sleeping):
                self.runtime.state = PetState(sleeping=sleeping)
                self.assertTrue(self.runtime.can_place_item)
                self.runtime.begin_carry("apple")
                token = self.cursor.instance_id
                assert token is not None
                self.assertFalse(self.runtime.can_place_item)
                self.cursor.release()
                self.assertEqual(self.world.get(token).state, ObjectState.FALLING)
                self.assertFalse(self.cursor.carrying)
        self.interaction.interrupt.assert_not_called()
        self.awareness.intentions.cancel.assert_not_called()
        self.walk.movement.set_goal.assert_not_called()
        self.behavior.request_orientation.assert_not_called()

    def test_second_request_preserves_the_held_portion_and_release_is_once(self):
        self.runtime.begin_carry("apple")
        token = self.cursor.instance_id
        snapshot = self.world.snapshot()
        self.runtime.begin_carry("apple")
        self.cursor.begin("apple")
        self.assertEqual(self.world.snapshot(), snapshot)
        self.assertEqual(self.cursor.instance_id, token)
        self.cursor.release()
        released = self.world.snapshot()
        self.cursor.release()
        self.assertEqual(self.world.snapshot(), released)
        self.ports.handover.assert_called_once_with(token)

    def test_foreign_capture_or_closed_runtime_rejects_placement(self):
        self.root.tk.call.return_value = ".other-window"
        self.assertFalse(self.runtime.can_place_item)
        self.runtime.begin_carry("apple")
        self.cursor.begin("apple")
        self.assertEqual(self.world.snapshot().objects, ())
        self.root.grab_set.assert_not_called()
        self.root.tk.call.return_value = ""
        self.runtime._closed = True
        self.runtime.begin_carry("apple")
        self.assertEqual(self.world.snapshot().objects, ())

    def test_existing_authorized_handover_keeps_single_custody_transfer(self):
        def handover(token):
            item = self.world.get(token)
            self.world.accept_handover_on_release(
                token, expected_revision=item.revision,
            )
            return True

        self.ports.handover.side_effect = handover
        self.runtime.begin_carry("apple")
        token = self.cursor.instance_id
        assert token is not None
        self.cursor.release()
        self.cursor.release()
        self.assertEqual(self.world.get(token).state, ObjectState.PET_HELD)
        self.ports.handover.assert_called_once_with(token)


class OfferFeedbackOwnershipTests(unittest.TestCase):
    def test_menu_and_offer_cancellation_do_not_hold_or_cancel_short_playback(self):
        scheduler = FakeScheduler()
        completed = MagicMock()
        player = ReactionPlayer(
            schedule=scheduler.schedule, cancel_timer=scheduler.cancel,
            display_emote=MagicMock(), display_text=MagicMock(),
            start_action=MagicMock(), mark_spoken=MagicMock(),
            is_closed=lambda: False,
        )
        presenter = ObjectFeedbackPresenter(player, MagicMock(spec=ItemCatalog))
        player.play(Reaction.spoken("care", "Hallo", "idle", "talk"),
                    on_complete=completed)
        self.assertTrue(player.active)
        self.assertFalse(player.story_active)
        self.assertTrue(presenter.non_offer_playback_active)
        presenter.cancel_offer()
        token = player.pending_timer
        assert token is not None
        scheduler.fire(token)
        self.assertFalse(player.active)
        self.assertFalse(presenter.non_offer_playback_active)
        completed.assert_called_once_with(True)
        player.play(Reaction.spoken("offer", "Keks?", "idle", "object_offer"))
        self.assertTrue(player.active)
        self.assertFalse(presenter.non_offer_playback_active)
        presenter.cancel_offer()
        self.assertFalse(player.active)

    def test_cancelled_cursor_gesture_preserves_unrelated_dialogue(self):
        player = MagicMock(spec=ReactionPlayer)
        presenter = ObjectFeedbackPresenter(player, MagicMock(spec=ItemCatalog))
        for event in ("pet", "talk", "object_notice", None):
            player.event = event
            presenter.cancel_offer()
        player.cancel.assert_not_called()
        for event in ("object_offer", "object_refuse"):
            player.event = event
            presenter.cancel_offer()
        self.assertEqual(player.cancel.call_count, 2)
