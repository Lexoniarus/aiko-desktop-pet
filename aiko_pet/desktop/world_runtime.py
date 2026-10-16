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
from ..application.object_feedback import FeedbackReceipt, ObjectFeedback
from ..application.object_interaction import ObjectInteractionCoordinator
from ..application.session import WorldSessionSnapshot
from ..application.settings import PetSettings
from ..infrastructure.active_time import active_uptime_seconds
from ..infrastructure.world_catalog import build_consumable_definitions
from ..pet.animation.character import FRAME_WIDTH, PlaybackEvent
from ..pet.animation.item_assets import ItemCatalog
from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.content import GERMAN_TEXT
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.catalog import Reaction
from ..pet.mind.object_decisions import ObjectUseDecision, decide_object_use
from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..pet.routine import context_at
from ..pet.state import PetState
from ..ui.pet_view.action_playback import ActionPlayback
from ..ui.pet_view.animated_pet import AnimatedPet
from ..ui.world_view import WorldView
from ..world.contracts import (
    ObjectFootprint,
    ObjectState,
    WorldSnapshot,
    WorldSurface,
)
from ..world.state import WorldOperationError, WorldState
from .cursor_item_gesture import CursorItemGesture, CursorItemPorts
from .geometry import GroundApproach, TaskbarTrack
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
        present_feedback: Callable[
            [ObjectFeedback, Reaction, Callable[[FeedbackReceipt], None]], None
        ], cancel_feedback: Callable[[], None], feedback: Callable[[str], None],
        save: Callable[[], None],
        restored_world: WorldSnapshot | None = None,
        restored_memory: ObjectMemorySnapshot | None = None,
    ) -> None:
        self.root, self.state, self.settings = root, state, settings
        self._track, self._walk, self._visual = track, walk, visual
        self._animated, self._playback = animated, playback
        self._inputs, self._game_open = inputs, game_open
        self._controls_active = controls_active
        self._present_feedback = present_feedback
        self._save, self._mind = save, mind
        self._care: CareOutcome | None = None
        self._cancel_feedback = cancel_feedback
        self.world = WorldState(self._surface(), build_consumable_definitions(
            DEFAULT_CATALOG, items,
        ))
        if restored_world is not None:
            self.world.restore_snapshot(restored_world)
            self.world.change_surface(self._surface())
        self.awareness = ObjectAwareness(
            restored_memory if restored_world is not None else None,
        )
        self._consumption = ObjectConsumption(
            state, mind, adaptive, clock=clock, memory=self.awareness.memory,
        )
        self.view = WorldView(root, items)
        self._refresh_footprints()
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
            can_acquire=self._can_acquire, ground_x=self._ground_x,
            completed=self._completed,
            memory=self.awareness.memory, decide=self._decide,
            feedback=self._phase_feedback, cancel_feedback=cancel_feedback,
            now=lambda: self.now, inspection_seconds=BALANCE.number(
                "object_behavior", "inspection_seconds",
            ),
        )
        animated.on_playback = self._queue_event
        self.cursor = CursorItemGesture(
            root=root, world=self.world, view=self.view, settings=settings,
            track=track, memory=self.awareness.memory,
            ports=CursorItemPorts(
                capture_contact=self._capture_contact,
                handover=self.interaction.offer_on_release,
                offer_wanted=self._offer_wanted, present_offer=self._present_offer,
                cancel_feedback=cancel_feedback, save=save, sync_view=self._sync_view,
                outside=lambda: feedback(GERMAN_TEXT.format("world.outside")),
            ),
        )
        self._timer = root.after(33, self._frame)

    def memory_snapshot(self) -> ObjectMemorySnapshot:
        return self.awareness.memory.export(now=self.now)

    def save_snapshot(self) -> WorldSessionSnapshot:
        return WorldSessionSnapshot(self.world.snapshot(), self.memory_snapshot(),
                                     self._body_x())

    def _surface(self) -> WorldSurface:
        track = self._track()
        return WorldSurface(max(1, track.right - track.left), max(1, track.ground_y))

    def _body_x(self) -> float:
        return (self.settings.x or 0) - self._track().left + self.width / 2

    @property
    def width(self) -> float:
        return FRAME_WIDTH * self.settings.scale

    def _play(self, clip: str) -> int:
        self._playback.start("pick_up" if clip == "hold_item" else clip, 0)
        if clip == "hold_item":
            self._animated.hold_last_pose("pick_up", time.monotonic())
        return self._animated.action_id

    def _decide(self, token: str, origin: ConsumptionOrigin) -> ObjectUseDecision:
        return decide_object_use(self.awareness.memory.get(token), self.state, origin)

    def _phase_feedback(self, cue: ObjectFeedback) -> None:
        reaction = self._care.reaction if (
            cue.event in ("object_finished_food", "object_finished_drink")
            and self._care is not None
        ) else None
        if reaction is None:
            reaction = self._mind.select_reaction(
                cue.event, self.state, context_at(time.time()), time.monotonic(),
            )
        if reaction is None:
            raise ValueError(f"Missing required object reaction: {cue.event}")
        self._present_feedback(cue, reaction, self._receive_feedback)

    def _receive_feedback(self, receipt: FeedbackReceipt) -> None:
        if not self._closed:
            self.interaction.receive_feedback(receipt)

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
        outcome = self._consumption.commit(
            self.world, key, token, origin,
            self._inputs(time.time(), time.monotonic()),
        )
        if outcome.accepted:
            self._save()
            if origin == ConsumptionOrigin.HANDOVER:
                self._care = outcome.care
        return outcome.accepted

    def _select_item(self, item_id: str | None) -> None:
        overlay = self._animated.food_overlay
        if item_id is not None and self._contact is not None:
            overlay.contact_origin = self._contact
        else:
            overlay.contact_origin = None
        overlay.select(item_id)

    def _completed(self, _token: str, consumed: bool) -> None:
        self.awareness.intentions.cancel(self.now, consumed=consumed)
        self._walk.movement.set_goal(None)
        self._visual.object_target = None
        self._contact = None
        self._care = None
        self._save()

    def _ground_x(self, token: str) -> float:
        item = self.world.get(token)
        surface = self.world.snapshot().surface
        return max(item.footprint.left,
                   min(self._body_x(), surface.width - item.footprint.right))

    def _ground_approach(self, x: float) -> GroundApproach | None:
        track = self._track()
        return track.ground_approach(
            track.left + x, int(self.width),
            self.width * BALANCE.number("object_behavior", "reach_widths"),
        )

    def _can_acquire(self, token: str) -> bool:
        if self.state.sleeping or self._game_open():
            return False
        try:
            item = self.world.get(token)
        except WorldOperationError:
            return False
        known = self.awareness.memory.get(token)
        if known is None or item.position is None:
            return False
        distance = abs(item.position.x - self._body_x())
        if item.state == ObjectState.USER_HELD:
            return (
                not self.interaction.active
                and self.cursor.offer_ready
                and decide_object_use(
                    known, self.state, ConsumptionOrigin.HANDOVER,
                ).consume
                and time.monotonic() >= self._playback.until
                and self.now - known.observed_at < 0.5
                and any(seen.token == token for seen in self.awareness.observations)
                and distance <= self.width * 0.3
                and self.width * 0.05 <= item.position.height <= self.width * 0.9
            )
        if self._controls_active():
            return False
        track = self._track()
        return item.state == ObjectState.RESTING and track.can_grasp_ground(
            track.left + item.position.x, self.settings.x or 0, int(self.width),
            self.width * BALANCE.number("object_behavior", "reach_widths"),
        )

    def _capture_contact(self, token: str) -> None:
        item = self.world.get(token)
        if item.position is None:
            return
        if item.state == ObjectState.RESTING:
            approach = self._ground_approach(item.position.x)
            if approach is not None and approach.edge_grip:
                # Frame 4 acquires directly at the authored hand anchor.
                self._contact = None
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
        self.interaction.update()
        blocked = ((self.interaction.active and not self.interaction.approaching)
                   or self.cursor.carrying or self._game_open()
                   or self._controls_active() or self.state.sleeping
                   or time.monotonic() < self._playback.until)
        snapshot = self.world.snapshot()
        if self.cursor.carrying and not self.cursor.inside:
            from dataclasses import replace

            snapshot = replace(snapshot, objects=tuple(
                item for item in snapshot.objects
                if item.instance_id != self.cursor.instance_id
            ))
        goal = self.awareness.update(
            snapshot, self.state, now=self.now, x=self._body_x(), height=0,
            width=self.width,
            attentive=not self.state.sleeping and not self._game_open(),
            blocked=blocked,
            held_pose=(self._body_x(), self.width * .4),
        )
        observed = {item.token for item in self.awareness.observations}
        visible = [item for item in self.awareness.memory.snapshot()
                   if not item.examined and item.token in observed]
        gaze = goal or (min(visible, key=lambda item: abs(item.x - self._body_x()))
                        if visible else None)
        self._visual.object_target = (
            (self._track().left + gaze.x, self._track().ground_y - gaze.height)
            if gaze is not None else None
        )
        self.cursor.observe_offer()
        if blocked or goal is None:
            self._walk.movement.set_goal(None)
            self._search_at = None
            if self.interaction.approaching:
                self.interaction.interrupt(lambda: None)
            return
        if not self.interaction.active:
            self.interaction.begin_goal(goal)
        if self.interaction.phase == "notice":
            self._walk.movement.set_goal(None)
            return
        approach = self._ground_approach(goal.x)
        if approach is None:
            self.awareness.intentions.cancel(self.now)
            self._walk.movement.set_goal(None)
            self.interaction.interrupt(lambda: None)
            return
        self._walk.movement.set_goal(approach.standing_x)
        if not approach.arrived(self.settings.x or 0):
            self._search_at = None
            return
        if self._can_acquire(goal.token):
            self._walk.movement.set_goal(None)
            self._capture_contact(goal.token)
            self.interaction.arrive()
            self._search_at = None
        else:
            self._search_at = self.now if self._search_at is None else self._search_at
            if self.now - self._search_at >= BALANCE.number(
                "object_behavior", "search_seconds",
            ):
                self.awareness.intentions.cancel(self.now)
                self._walk.movement.set_goal(None)
                self._visual.object_target = None
                self.interaction.missing()

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
        self.interrupt(lambda: self.cursor.begin(item_id))

    def _offer_wanted(self, token: str) -> bool:
        return (decide_object_use(
            self.awareness.memory.get(token), self.state, ConsumptionOrigin.HANDOVER,
        ).consume and not self._game_open() and not self.interaction.active
            and time.monotonic() >= self._playback.until)

    def _present_offer(self, cue: ObjectFeedback) -> None:
        reaction = self._mind.select_reaction(
            cue.event, self.state, context_at(time.time()), time.monotonic(),
        )
        if reaction is None:
            raise ValueError("Missing required offer reaction")
        self._present_feedback(cue, reaction, lambda _receipt: None)

    def _sync_view(self) -> None:
        self.view.sync(self.world.snapshot(), left=self._track().left,
                       ground_y=self._track().ground_y, scale=self.settings.scale,
                       topmost=self.settings.always_on_top,
                       carried_cursor=(self.root.winfo_pointerx(),
                                       self.root.winfo_pointery())
                       if self.cursor.carrying else None)
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
        self.cursor.update()
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
        self._cancel_feedback()
        self.cursor.close()
        for timer in (self._timer, self._event_timer):
            if timer is not None:
                self.root.after_cancel(timer)
        self._animated.on_playback = lambda _event: None
        self.view.close()
