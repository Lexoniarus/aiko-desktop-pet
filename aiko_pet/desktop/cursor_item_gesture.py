"""Own one cursor gesture, native input capture and release/cancellation."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from ..application.object_feedback import FeedbackKey, ObjectFeedback
from ..application.settings import PetSettings
from ..pet.mind.object_memory import ObjectMemory
from ..ui.world_view import WorldView
from ..world.contracts import ObjectFootprint, WorldPosition
from ..world.state import WorldState
from .geometry import TaskbarTrack
from .global_input import mouse_buttons_down_windows


@dataclass(frozen=True, slots=True)
class CursorItemPorts:
    capture_contact: Callable[[str], None]
    handover: Callable[[str], bool]
    offer_wanted: Callable[[str], bool]
    present_offer: Callable[[ObjectFeedback], None]
    cancel_feedback: Callable[[], None]
    save: Callable[[], None]
    sync_view: Callable[[], None]
    outside: Callable[[], None]


class CursorItemGesture:
    def __init__(
        self, *, root: tk.Tk, world: WorldState, view: WorldView,
        settings: PetSettings, track: Callable[[], TaskbarTrack],
        memory: ObjectMemory, ports: CursorItemPorts,
    ) -> None:
        self.root, self.world, self.view, self.settings = root, world, view, settings
        self._track, self._memory, self._ports = track, memory, ports
        self.instance_id: str | None = None
        self.inside = True
        self.offer_ready = False
        self._capture_owned = False
        self._offer_feedback: tuple[str, bool] | None = None
        self._offer_serial = self._offer_revision = 0
        root.bind_all("<Escape>", lambda _event: self.cancel(), add="+")
        root.bind_all("<ButtonRelease-1>", lambda _event: self.release(), add="+")

    @property
    def carrying(self) -> bool:
        return self.instance_id is not None

    def begin(self, item_id: str) -> None:
        self.cancel()
        self._offer_feedback = None
        self.offer_ready = False
        self._offer_serial += 1
        image = self.view.image(item_id, self.settings.scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        position, self.inside = self._pointer_pose(item_id, footprint)
        item = self.world.create_held(item_id, position, footprint)
        self.instance_id = item.instance_id
        try:
            self.root.grab_set()
            self.root.focus_set()
            self._capture_owned = True
        except tk.TclError:
            self.cancel()
            return
        self._ports.sync_view()

    def observe_offer(self) -> None:
        token = self.instance_id
        known = self._memory.get(token) if token is not None else None
        if token is None or known is None or known.identity is None:
            return
        wanted = self._ports.offer_wanted(token)
        if self._offer_feedback == (token, wanted):
            return
        self._offer_feedback = token, wanted
        self.offer_ready = wanted
        self._offer_revision += 1
        key = FeedbackKey(f"offer_{self._offer_serial}", self._offer_revision)
        cue = ObjectFeedback(key, "object_offer" if wanted else "object_refuse",
                             token, known.identity)
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
        inside = (footprint.left <= x <= surface.width - footprint.right
                  and 0 <= height <= surface.height)
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
            self.world.remove(token, expected_revision=item.revision)
            self._ports.outside()
        else:
            self._ports.capture_contact(token)
            if not self._ports.handover(token):
                self.world.release(token, expected_revision=item.revision)
        self._ports.save()

    def cancel(self) -> None:
        self._release_capture()
        if self.instance_id is not None:
            item = self.world.get(self.instance_id)
            self.world.remove(item.instance_id, expected_revision=item.revision)
            self.instance_id = None
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
