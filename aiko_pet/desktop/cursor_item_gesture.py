"""Own one cursor gesture, native input capture and release/cancellation."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from ..application.object_feedback import FeedbackKey, ObjectFeedback
from ..application.settings import PetSettings
from ..pet.mind.object_decisions import ObjectUseDecision
from ..pet.mind.object_knowledge import ObjectKnowledge
from ..ui.world_view import WorldView
from ..world.contracts import ObjectFootprint, WorldPosition
from ..world.state import WorldOperationError, WorldState
from .geometry import TaskbarTrack
from .global_input import mouse_buttons_down_windows


@dataclass(frozen=True, slots=True)
class CursorItemPorts:
    capture_contact: Callable[[str], None]
    handover: Callable[[str], bool]
    assess_offer: Callable[[str], ObjectUseDecision | None]
    known_instance: Callable[[str], ObjectKnowledge | None]
    present_offer: Callable[[ObjectFeedback], None]
    cancel_feedback: Callable[[], None]
    save: Callable[[], None]
    sync_view: Callable[[], None]
    outside: Callable[[], None]


class CursorItemGesture:
    def __init__(
        self, *, root: tk.Tk, world: WorldState, view: WorldView,
        settings: PetSettings, track: Callable[[], TaskbarTrack],
        ports: CursorItemPorts,
    ) -> None:
        self.root, self.world, self.view, self.settings = root, world, view, settings
        self._track, self._ports = track, ports
        self.instance_id: str | None = None
        self.inside = True
        self.offer_ready = False
        self._capture_owned = False
        self._offer_feedback: tuple[str, bool] | None = None
        self._offer_serial = self._offer_revision = 0
        self._return_x: float | None = None
        root.bind_all("<Escape>", lambda _event: self.cancel(), add="+")
        root.bind_all("<ButtonRelease-1>", lambda _event: self.release(), add="+")

    @property
    def carrying(self) -> bool:
        return self.instance_id is not None

    def begin(self, item_id: str) -> None:
        self.cancel()
        self._return_x = None
        image = self.view.image(item_id, self.settings.scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        position, self.inside = self._pointer_pose(item_id, footprint)
        item = self.world.create_held(item_id, position, footprint)
        self._start(item.instance_id)

    def begin_existing(self, token: str, expected_revision: int) -> bool:
        if self.carrying:
            return False
        try:
            item = self.world.take_resting(token, expected_revision=expected_revision)
        except WorldOperationError:
            return False
        assert item.position is not None
        self._return_x = item.position.x
        self._start(token)
        return self.carrying

    def _start(self, token: str) -> None:
        self._offer_feedback = None
        self.offer_ready = False
        self._offer_serial += 1
        self.instance_id = token
        try:
            self.root.grab_set()
            self.root.focus_set()
            self._capture_owned = True
        except tk.TclError:
            self.cancel()
            return
        self._move_carry()
        self._ports.save()
        self._ports.sync_view()

    def observe_offer(self) -> None:
        token = self.instance_id
        known = self._ports.known_instance(token) if token is not None else None
        if token is None or known is None or known.identity is None:
            self.offer_ready = False
            return
        decision = self._ports.assess_offer(token)
        self.offer_ready = decision is not None and decision.consume
        if decision is None:
            return
        wanted = decision.consume
        if self._offer_feedback == (known.token, wanted):
            return
        self._offer_feedback = known.token, wanted
        self._offer_revision += 1
        key = FeedbackKey(f"offer_{self._offer_serial}", self._offer_revision)
        cue = ObjectFeedback(key, "object_offer" if wanted else "object_refuse",
                             known.token, known.identity)
        # Preview completion never grants custody or willingness.
        self._ports.present_offer(cue)

    def _release_capture(self) -> None:
        if self._capture_owned:
            self._capture_owned = False
            if self._owns_capture():
                self.root.grab_release()

    def _owns_capture(self) -> bool:
        current = self.root.tk.call("grab", "current", str(self.root))
        return str(current) == str(self.root)

    def _pointer_pose(
        self, item_id: str, footprint: ObjectFootprint,
    ) -> tuple[WorldPosition, bool]:
        image = self.view.image(item_id, self.settings.scale)
        sprite = self.view.items.foods[item_id].sprites[self.settings.scale]
        track = self._track()
        surface = self.world.snapshot().surface
        x = (self.root.winfo_pointerx() - track.left
             + image.width() / 2 - sprite.pivot[0])
        height: float = track.ground_y - self.root.winfo_pointery() - image.height()
        height += sprite.pivot[1]
        inside = (track.left <= self.root.winfo_pointerx() < track.right
                  and 0 <= self.root.winfo_pointery() < self.root.winfo_screenheight())
        return WorldPosition(
            max(footprint.left, min(x, surface.width - footprint.right)),
            max(0, min(height, surface.height)),
        ), inside

    def _move_carry(self) -> None:
        if self.instance_id is None:
            return
        item = self.world.get(self.instance_id)
        position, self.inside = self._pointer_pose(item.definition_id, item.footprint)
        self.world.move_held(item.instance_id, position,
                             expected_revision=item.revision)

    def release(self) -> None:
        if self.instance_id is None:
            return
        self._move_carry()
        token, self.instance_id = self.instance_id, None
        self._release_capture()
        item = self.world.get(token)
        if not self.inside:
            self._discard_or_return(token, item.revision)
            self._ports.outside()
        else:
            self._ports.capture_contact(token)
            if not self._ports.handover(token):
                self.world.release(token, expected_revision=item.revision)
        self._return_x = None
        self.offer_ready = False
        self._ports.save()

    def _discard_or_return(self, token: str, revision: int) -> None:
        if self._return_x is None:
            self.world.remove(token, expected_revision=revision)
        else:
            self.world.return_user_held(token, self._return_x,
                                        expected_revision=revision)

    def cancel(self) -> None:
        self._release_capture()
        if self.instance_id is not None:
            item = self.world.get(self.instance_id)
            self._discard_or_return(item.instance_id, item.revision)
            self.instance_id = None
            self._return_x = None
            self.offer_ready = False
            self._ports.cancel_feedback()
            self._ports.save()

    def update(self) -> None:
        if self.carrying and self._capture_owned and not self._owns_capture():
            self.cancel()
        self._move_carry()
        buttons = mouse_buttons_down_windows()
        if self.carrying and buttons is not None and not buttons[0]:
            self.release()

    def close(self) -> None:
        # Session persistence normalizes unfinished cursor custody on restart.
        self._release_capture()
