"""Desktop adapters for World time, observation, input and presentation.

    Pet decisions and interaction execution remain in their owning packages.
"""

from __future__ import annotations

import time
import tkinter as tk
from collections import deque
from collections.abc import Callable

from ..application.active_time import ActiveSessionClock, SessionInputs
from ..application.controller import CareOutcome
from ..application.object_awareness import ObjectAwareness
from ..application.object_consumption import ObjectConsumption
from ..application.object_interaction import ObjectInteractionCoordinator
from ..application.settings import PetSettings
from ..infrastructure.active_time import active_uptime_seconds
from ..infrastructure.world_catalog import build_consumable_definitions
from ..pet.animation.character import FRAME_WIDTH, PlaybackEvent
from ..pet.animation.item_assets import ItemCatalog
from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.content import GERMAN_TEXT
from ..pet.food import FOOD_BALANCE
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.state import PetState
from ..ui.pet_view.action_playback import ActionPlayback
from ..ui.pet_view.animated_pet import AnimatedPet
from ..ui.world_view import WorldView
from ..world.contracts import (
    ObjectFootprint,
    ObjectState,
    WorldPosition,
    WorldSnapshot,
    WorldSurface,
)
from ..world.state import WorldState
from .geometry import TaskbarTrack
from .global_input import mouse_buttons_down_windows
from .visual_observation import DesktopVisualObservation
from .walk_runtime import WalkDriver


class DesktopWorldRuntime:
    def __init__(
        self, *, root: tk.Tk, state: PetState, settings: PetSettings,
        mind: PetMind, adaptive: AdaptiveRoutine, items: ItemCatalog,
        clock: ActiveSessionClock, track: Callable[[], TaskbarTrack],
        walk: WalkDriver, visual: DesktopVisualObservation, animated: AnimatedPet,
        playback: ActionPlayback, inputs: Callable[[float, float], SessionInputs],
        game_open: Callable[[], bool], controls_active: Callable[[], bool],
        show_care: Callable[[CareOutcome], None], feedback: Callable[[str], None],
        save: Callable[[], None],
        restored_world: WorldSnapshot | None = None,
    ) -> None:
        self.root, self.state, self.settings = root, state, settings
        self._track, self._walk, self._visual = track, walk, visual
        self._animated, self._playback = animated, playback
        self._inputs, self._game_open = inputs, game_open
        self._controls_active = controls_active
        self._show_care, self._feedback, self._save = show_care, feedback, save
        self.world = WorldState(self._surface(), build_consumable_definitions(
            DEFAULT_CATALOG, items,
        ))
        if restored_world is not None:
            self.world.restore_snapshot(restored_world)
            self.world.change_surface(self._surface())
        self.awareness = ObjectAwareness()
        self._consumption = ObjectConsumption(state, mind, adaptive, clock=clock)
        self.view = WorldView(root, items)
        self._refresh_footprints()
        self.carry_id: str | None = None
        self._capture_owned = False
        self._inside = True
        self._contact: tuple[float, float] | None = None
        self._closed = False
        self.user_action_pending = False
        self._last_scale = settings.scale
        self._last_active = active_uptime_seconds()
        self._last_real = time.monotonic()
        self.now = 0.0
        self._search_at: float | None = None
        self._timer: str | None = None
        self._event_timer: str | None = None
        self._events: deque[PlaybackEvent] = deque(maxlen=128)
        self.interaction = ObjectInteractionCoordinator(
            self.world, play=self._play, stop=self._stop,
            select_item=self._select_item, consume=self._consume,
            eligible=self._eligible, ground_x=self._ground_x,
            completed=self._completed,
        )
        animated.on_playback = self._queue_event
        root.bind_all("<Escape>", lambda _event: self.cancel_carry(), add="+")
        root.bind_all("<ButtonRelease-1>", lambda _event: self.release(), add="+")
        self._timer = root.after(33, self._frame)

    @property
    def carrying(self) -> bool:
        return self.carry_id is not None

    def _surface(self) -> WorldSurface:
        track = self._track()
        return WorldSurface(max(1, track.right - track.left), max(1, track.ground_y))

    def _body_x(self) -> float:
        return (self.settings.x or 0) - self._track().left + self.width / 2

    @property
    def width(self) -> float:
        return FRAME_WIDTH * self.settings.scale

    def _play(self, clip: str) -> int:
        self._playback.start(clip, 0)
        return self._animated.action_id

    def _stop(self) -> None:
        self._playback.cancel_at(time.monotonic())

    def _queue_event(self, event: PlaybackEvent) -> None:
        if self._closed:
            return
        self._events.append(event)
        if self._event_timer is None:
            self._event_timer = self.root.after_idle(self._drain_events)

    def _drain_events(self) -> None:
        self._event_timer = None
        while self._events and not self._closed:
            self.interaction.receive(self._events.popleft())

    def _consume(self, key: str, token: str, origin: ConsumptionOrigin) -> bool:
        outcome = self._consumption.complete(
            self.world, key, token, origin,
            self._inputs(time.time(), time.monotonic()),
        )
        if outcome.accepted:
            self._save()
            if origin == ConsumptionOrigin.HANDOVER and outcome.care is not None:
                self._show_care(outcome.care)
        return outcome.accepted

    def _select_item(self, item_id: str | None) -> None:
        overlay = self._animated.food_overlay
        if item_id is not None and self._contact is not None:
            overlay.contact_origin = self._contact
        else:
            overlay.contact_origin = None
        overlay.select(item_id)

    def _completed(self, token: str, consumed: bool) -> None:
        if consumed:
            self.awareness.memory.forget(token)
        self.awareness.intentions.cancel(self.now, consumed=consumed)
        self._walk.movement.set_goal(None)
        self._visual.object_target = None
        self._contact = None
        self._save()

    def _ground_x(self, token: str) -> float:
        item = self.world.get(token)
        surface = self.world.snapshot().surface
        return max(item.footprint.left,
                   min(self._body_x(), surface.width - item.footprint.right))

    def _eligible(self, token: str) -> bool:
        if self.state.sleeping or self._game_open():
            return False
        item = self.world.get(token)
        known = next((known for known in self.awareness.memory.snapshot()
                      if known.token == token and known.identity is not None), None)
        if known is None or item.position is None:
            return False
        drink = item.definition_id == "energy_drink"
        if (self.state.energy >= 100 if drink else
                self.state.satiety >= FOOD_BALANCE.too_full_to_eat_threshold):
            return False
        distance = abs(item.position.x - self._body_x())
        if item.state == ObjectState.USER_HELD:
            return (
                not self.interaction.active
                and time.monotonic() >= self._playback.until
                and self.now - known.observed_at < 0.5
                and distance <= self.width * 0.3
                and self.width * 0.05 <= item.position.height <= self.width * 0.9
            )
        if self._controls_active():
            return False
        threshold = BALANCE.number(
            "object_behavior", "seek_drink_energy" if drink else "seek_food_satiety",
        )
        level = self.state.energy if drink else self.state.satiety
        return (item.state == ObjectState.RESTING and level <= threshold
                and distance <= self.width * BALANCE.number(
                    "object_behavior", "reach_widths",
                ))

    def _capture_contact(self, token: str) -> None:
        item = self.world.get(token)
        if item.position is None:
            return
        sprite = self.view.items.foods[item.definition_id].sprites[self.settings.scale]
        image = self.view.image(item.definition_id, self.settings.scale)
        self._contact = (
            self._track().left + item.position.x - image.width() / 2
            + sprite.pivot[0] - (self.settings.x or 0),
            self._track().ground_y - item.position.height - image.height()
            + sprite.pivot[1] - (self.settings.y or 0),
        )

    def update(self, _now: float) -> None:
        if self._closed:
            return
        blocked = (self.interaction.active or self.carrying or self._game_open()
                   or self._controls_active() or self.state.sleeping
                   or time.monotonic() < self._playback.until)
        snapshot = self.world.snapshot()
        if self.carrying and not self._inside:
            from dataclasses import replace

            snapshot = replace(snapshot, objects=tuple(
                item for item in snapshot.objects if item.instance_id != self.carry_id
            ))
        goal = self.awareness.update(
            snapshot, self.state, now=self.now, x=self._body_x(), height=0,
            width=self.width,
            attentive=not self.state.sleeping and not self._game_open(),
            blocked=blocked,
        )
        visible = [item for item in self.awareness.memory.snapshot()
                   if self.now - item.observed_at < 0.5]
        gaze = goal or (min(visible, key=lambda item: abs(item.x - self._body_x()))
                        if visible else None)
        self._visual.object_target = (
            (self._track().left + gaze.x, self._track().ground_y - gaze.height)
            if gaze is not None else None
        )
        if blocked or goal is None:
            self._walk.movement.set_goal(None)
            self._search_at = None
            return
        track = self._track()
        target = max(track.left, min(track.left + goal.x - self.width / 2,
                                     track.right - self.width))
        if abs(target + self.width / 2 - track.left - goal.x) > self.width * 0.25:
            self.awareness.intentions.cancel(self.now)
            return
        self._walk.movement.set_goal(target)
        if abs((self.settings.x or 0) - target) > 2:
            self._search_at = None
            return
        if self._eligible(goal.token):
            self._walk.movement.set_goal(None)
            self._capture_contact(goal.token)
            self.interaction.begin_pickup(goal.token)
            self._search_at = None
        else:
            self._search_at = self.now if self._search_at is None else self._search_at
            if self.now - self._search_at >= BALANCE.number(
                "object_behavior", "search_seconds",
            ):
                self.awareness.memory.forget(goal.token)
                self.awareness.intentions.cancel(self.now)
                self._walk.movement.set_goal(None)

    def interrupt(self, action: Callable[[], None]) -> None:
        self.awareness.intentions.cancel(self.now)
        self._walk.movement.set_goal(None)
        self._visual.object_target = None
        self.user_action_pending = True

        def perform() -> None:
            try:
                action()
            finally:
                self.user_action_pending = False

        self.interaction.interrupt(perform)

    def begin_carry(self, item_id: str) -> None:
        self.interrupt(lambda: self._begin_carry_now(item_id))

    def _begin_carry_now(self, item_id: str) -> None:
        self.cancel_carry()
        image = self.view.image(item_id, self.settings.scale)
        footprint = ObjectFootprint(image.width() / 2, image.width() / 2)
        position, self._inside = self._pointer_pose(item_id, footprint)
        item = self.world.create_held(item_id, position, footprint)
        self.carry_id = item.instance_id
        try:
            self.root.grab_set()
            self.root.focus_set()
            self._capture_owned = True
        except tk.TclError:
            self.cancel_carry()
            return
        self._sync_view()

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
        if self.carry_id is None:
            return
        item = self.world.get(self.carry_id)
        position, self._inside = self._pointer_pose(item.definition_id, item.footprint)
        self.world.move_held(item.instance_id, position,
                             expected_revision=item.revision)

    def release(self) -> None:
        if self.carry_id is None:
            return
        self._move_carry()
        token, self.carry_id = self.carry_id, None
        self._release_capture()
        item = self.world.get(token)
        if not self._inside:
            self.world.remove(token, expected_revision=item.revision)
            self._feedback(GERMAN_TEXT.format("world.outside"))
        else:
            self._capture_contact(token)
            if not self.interaction.offer_on_release(token):
                self.world.release(token, expected_revision=item.revision)
        self._save()

    def cancel_carry(self) -> None:
        self._release_capture()
        if self.carry_id is not None:
            item = self.world.get(self.carry_id)
            self.world.remove(item.instance_id, expected_revision=item.revision)
            self.carry_id = None
            self._save()

    def _sync_view(self) -> None:
        self.view.sync(self.world.snapshot(), left=self._track().left,
                       ground_y=self._track().ground_y, scale=self.settings.scale,
                       topmost=self.settings.always_on_top,
                       carried_cursor=(self.root.winfo_pointerx(),
                                       self.root.winfo_pointery()) if self.carrying
                       else None)
        state, _fixed = self._animated.frame_clock.active_key or ("idle", None)
        clip = self._animated.assets.clips[state]
        index = clip.sprite_index(self._animated.frame_clock.frame_index)
        self._animated.food_overlay.render(clip, clip.frames[index],
                                          scale=self.settings.scale)

    def _frame(self) -> None:
        self._timer = None
        if self._closed:
            return
        active, real = active_uptime_seconds(), time.monotonic()
        elapsed = (max(0, active - self._last_active)
                   if active is not None and self._last_active is not None
                   else min(0.5, max(0, real - self._last_real)))
        self._last_active, self._last_real = active, real
        self.now += elapsed
        self.world.change_surface(self._surface())
        if self._last_scale != self.settings.scale:
            self._refresh_footprints()
            self._last_scale = self.settings.scale
        self.world.advance_falls(elapsed, gravity=BALANCE.number(
            "object_behavior", "fall_gravity",
        ))
        if self.carrying and self._capture_owned and not self._owns_capture():
            self.cancel_carry()
        self._move_carry()
        buttons = mouse_buttons_down_windows()
        if self.carrying and buttons is not None and not buttons[0]:
            self.release()
        self._sync_view()
        self._timer = self.root.after(33, self._frame)

    def _refresh_footprints(self) -> None:
        for item in self.world.snapshot().objects:
            if item.state in (ObjectState.CONSUMED, ObjectState.REMOVED):
                continue
            image = self.view.image(item.definition_id, self.settings.scale)
            self.world.change_footprint(
                item.instance_id, ObjectFootprint(image.width() / 2, image.width() / 2),
                expected_revision=item.revision,
            )

    def close(self) -> None:
        self._closed = True
        self._release_capture()
        for timer in (self._timer, self._event_timer):
            if timer is not None:
                self.root.after_cancel(timer)
        self._animated.on_playback = lambda _event: None
        self.view.close()
