"""Menu admission and finite snack placement without Tk or native input."""

import tkinter as tk
import unittest
from typing import cast
from unittest.mock import MagicMock, patch

from aiko_pet.application.active_time import ActiveSessionClock, SessionInputs
from aiko_pet.application.object_awareness import ObjectAwareness
from aiko_pet.application.object_consumption import ObjectConsumption
from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.cursor_item_gesture import CursorItemGesture, CursorItemPorts
from aiko_pet.desktop.world_runtime import DesktopWorldRuntime
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.pet_codec import decode_pet_state, encode_pet_state
from aiko_pet.pet.animation.item_assets import ItemCatalog
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.catalog import Reaction
from aiko_pet.pet.mind.object_memory import ObjectMemory
from aiko_pet.pet.mind.object_perception import ObjectObservation
from aiko_pet.pet.state import PetState
from aiko_pet.pet.wish_catalog import WISH_CATALOG
from aiko_pet.pet.wishes import ActiveWish, WishArea, WishId, WishState
from aiko_pet.ui.common.image_button import ImageButton
from aiko_pet.ui.pet_view.object_feedback_presenter import ObjectFeedbackPresenter
from aiko_pet.ui.pet_view.reaction_player import ReactionPlayer
from aiko_pet.ui.windows.action_toolbar import ActionToolbar
from aiko_pet.ui.windows.hover_contracts import HoverActions
from aiko_pet.world.contracts import (
    ObjectDefinition,
    ObjectFootprint,
    ObjectInteraction,
    ObjectState,
    WorldPosition,
    WorldSurface,
)
from aiko_pet.world.state import WorldState
from tools.pet_test_support import object_test_attention
from tools.reaction_test_support import FakeScheduler


class MenuAdmissionTests(unittest.TestCase):
    def test_toolbar_displays_separate_placement_and_care_capabilities(self):
        toolbar = ActionToolbar.__new__(ActionToolbar)
        toolbar._actions = MagicMock(spec=HoverActions)
        toolbar._actions.can_interact.return_value = False
        toolbar._actions.can_place_item.return_value = True
        buttons = {action: MagicMock() for action in ("place_item", "pet")}
        buttons["place_item"].cget.return_value = "disabled"
        buttons["pet"].cget.return_value = "normal"
        toolbar.buttons = cast(dict[str, ImageButton], buttons)
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
            self.root.tk.call,
            "return_value",
            str(self.root),
        )
        self.root.grab_release.side_effect = lambda: setattr(
            self.root.tk.call,
            "return_value",
            "",
        )
        self.world = WorldState(
            WorldSurface(800, 600),
            (
                ObjectDefinition(
                    "apple",
                    "apple",
                    "apple",
                    frozenset((ObjectInteraction.EAT,)),
                ),
            ),
        )
        self.ports = MagicMock(spec=CursorItemPorts)
        self.ports.handover.return_value = False
        self.cursor = CursorItemGesture(
            root=self.root,
            world=self.world,
            view=MagicMock(),
            settings=PetSettings(),
            track=MagicMock(),
            ports=self.ports,
        )
        self.cursor.view.image = MagicMock()
        self.cursor.view.image.return_value.width.return_value = 16
        self.enterContext(
            patch.object(
                self.cursor,
                "_pointer_pose",
                return_value=(WorldPosition(100, 0), True),
            )
        )
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

    def test_quick_cancel_withdraws_queued_loss_before_first_gesture_save(self):
        awareness, pet = ObjectAwareness(), PetState()
        item = self.world.place_resting("apple", 100, ObjectFootprint(8, 8))
        record = awareness.memory.observe_find(ObjectObservation(
            "known", "apple", "food", 100, 0, True, 0,
        ), now=0, record="known", claimed=frozenset(), maximum_distance=0,
            instance_id=item.instance_id)
        displaced = self.world.move_resting(item.instance_id, 700, expected_revision=0)
        for now in (0, .3, .6):
            awareness.update(self.world.snapshot(), pet, now=now, x=100, height=0,
                             width=100, blocked=True,
                             attention=object_test_attention(100, width=100,
                                                              direction=(-1, 0)))
        self.assertEqual(len(awareness.absences), 1)
        returned = self.world.move_resting(item.instance_id, 100,
                                           expected_revision=displaced.revision)
        self.ports.existing_taken.side_effect = awareness.suspend_absence
        saved = []
        self.ports.save.side_effect = lambda: saved.append(awareness.memory.snapshot())
        self.assertFalse(self.cursor.begin_existing(item.instance_id, 0))
        self.assertEqual(len(awareness.absences), 1)
        self.ports.existing_taken.assert_not_called()
        self.assertTrue(self.cursor.begin_existing(item.instance_id, returned.revision))
        self.assertFalse(awareness.absences)
        self.cursor.cancel()  # No sensor update between take and cancellation.
        self.ports.existing_taken.assert_called_once_with(item.instance_id)
        self.assertEqual(len(saved), 2)
        self.assertTrue(all(entry.place_status == "remembered"
                            for snapshot in saved for entry in snapshot))
        for now in (.9, 1.2, 1.5):
            awareness.update(self.world.snapshot(), pet, now=now, x=100, height=0,
                             width=100, blocked=False,
                             attention=object_test_attention(100, width=100))
        self.assertFalse(awareness.absences)
        self.assertFalse(awareness.checking_absence)
        known = awareness.memory.get(record)
        assert known is not None
        self.assertEqual((known.x, known.place_status), (100, "remembered"))
        self.assertEqual(self.world.get(item.instance_id).position,
                         WorldPosition(100, 0))

    def test_only_perceived_release_fulfills_avoidance_even_when_declined(self):
        for mode in ("declined", "unperceived", "ground", "cancelled"):
            with self.subTest(mode=mode):
                pet = PetState(updated_at=1800000000, lived_seconds=100, satiety=100,
                               friendship=50, wishes=WishState(2, (ActiveWish(
                                   1, WishId.AVOID_FOOD, "apple", 0, 14400,
                                   goal=WISH_CATALOG.definitions[WishId.AVOID_FOOD].goal,
                                   pinned=True,
                               ),), ((WishArea.FOOD, 0),)))
                memory = ObjectMemory()
                self.runtime.state = pet
                self.runtime.world = self.world
                self.runtime.settings = PetSettings(scale=1)
                self.runtime._body_x = MagicMock(return_value=100)
                self.runtime._consumption = ObjectConsumption(
                    pet, make_aiko_mind(started_at=0), AdaptiveRoutine(),
                    clock=ActiveSessionClock(lambda: 0), memory=memory,
                )
                self.runtime._inputs = MagicMock(return_value=SessionInputs(
                    1800000000, 0, False, None, False, False, None,
                ))
                decision = None if mode == "unperceived" else MagicMock(consume=False)
                self.runtime._assess_offer = MagicMock(return_value=decision)
                self.interaction.offer_on_release.return_value = False
                self.ports.handover.side_effect = self.runtime._handover_on_release
                self.ports.assess_offer.return_value = decision
                position = WorldPosition(100, 0 if mode == "ground" else 70)
                with patch.object(self.cursor, "_pointer_pose",
                                  return_value=(position, True)):
                    self.cursor.begin("apple")
                    token = self.cursor.instance_id
                    assert token is not None
                    memory.update((ObjectObservation(token, "apple", "food",
                                                      100, 70, False, 0),), now=0)
                    known = memory.get(token)
                    self.awareness.known_instance.return_value = known
                    self.ports.known_instance.return_value = known
                    self.cursor.observe_offer()
                    self.assertTrue(pet.wishes.active)  # Preview is not handover.
                    if mode == "cancelled":
                        self.cursor.cancel()
                    else:
                        self.cursor.release()
                self.assertEqual(pet.satiety, 100)
                self.assertIsNone(pet.friendship_history.last_contact)
                self.assertEqual(bool(pet.wishes.active), mode != "declined")
                if mode == "declined":
                    cause = pet.moodlets.active[0].causes[0]
                    self.assertEqual(cause.object_id, token)
                    self.assertEqual([r.kind for r in pet.friendship_history.rewards],
                                     [])
                    loaded = decode_pet_state(encode_pet_state(pet), now=1800000000)
                    self.assertEqual(loaded.wishes, pet.wishes)
                    self.assertEqual(loaded.moodlets, pet.moodlets)

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
                token,
                expected_revision=item.revision,
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
            schedule=scheduler.schedule,
            cancel_timer=scheduler.cancel,
            display_emote=MagicMock(),
            display_text=MagicMock(),
            start_action=MagicMock(),
            mark_spoken=MagicMock(),
            is_closed=lambda: False,
        )
        presenter = ObjectFeedbackPresenter(player, MagicMock(spec=ItemCatalog))
        player.play(
            Reaction.spoken("care", "Hallo", "idle", "talk"), on_complete=completed
        )
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
