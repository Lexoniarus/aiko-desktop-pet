"""Desktop adapters for World time, observation, input and presentation.

    Pet decisions and interaction execution remain in their owning packages.
"""

from __future__ import annotations

import time
import tkinter as tk
from collections import deque
from collections.abc import Callable
from dataclasses import replace

from ..application.active_time import ActiveSessionClock, SessionInputs
from ..application.controller import CareOutcome
from ..application.object_awareness import (
    ObjectAwareness,
    held_type_conflicts_with_memory,
)
from ..application.object_behavior import (
    BehaviorFacts,
    Hold,
    ObjectBehaviorCoordinator,
    SearchMotion,
)
from ..application.object_consumption import ObjectConsumption
from ..application.object_feedback import FeedbackReceipt, ObjectFeedback
from ..application.object_interaction import ObjectInteractionCoordinator
from ..application.object_interaction_state import SearchPosition
from ..application.object_relationship import ObjectRelationship
from ..application.object_status import ObjectStatusSnapshot, snapshot_object_status
from ..application.session import WorldSessionSnapshot
from ..application.session_time import SessionTimeProgression
from ..application.settings import PetSettings
from ..infrastructure.active_time import active_uptime_seconds
from ..infrastructure.world_catalog import build_consumable_definitions
from ..infrastructure.world_motion import motion_parameters
from ..pet.animation.character import FRAME_WIDTH, PlaybackEvent
from ..pet.animation.item_assets import ItemCatalog
from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.content import GERMAN_TEXT
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.catalog import Reaction
from ..pet.mind.object_attention import LookSide, ObjectAttention
from ..pet.mind.object_decisions import (
    ObjectUseContext,
    ObjectUseDecision,
)
from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..pet.routine import context_at
from ..pet.sleep import sleep_care_complete
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
from .global_input import mouse_buttons_down_windows
from .visual_observation import DesktopVisualObservation
from .walk_runtime import WalkDriver


class DesktopWorldRuntime:
    def defer_sleep(self) -> bool:
        return (self.interaction.active or self.user_action_pending
                or self._game_open())

    def object_status(self) -> ObjectStatusSnapshot:
        return snapshot_object_status(
            self.world.snapshot(), self.awareness.memory.snapshot(),
        )

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
        self._motion_parameters = motion_parameters()
        self.world = WorldState(self._surface(), build_consumable_definitions(
            DEFAULT_CATALOG, items,
        ))
        if restored_world is not None:
            self.world.restore_snapshot(restored_world)
            self.world.change_surface(self._surface(), recovering=True)
        self.awareness = ObjectAwareness(
            restored_memory if restored_world is not None else None,
        )
        self.time_progression = SessionTimeProgression(
            self.world, self.awareness.memory,
        )
        self._consumption = ObjectConsumption(
            state, mind, adaptive, clock=clock, memory=self.awareness.memory,
            progression=self.time_progression,
        )
        self._relationship = ObjectRelationship(state, mind)
        self.view = WorldView(root, items, pickup=self.begin_relocate)
        self._refresh_footprints()
        self._contact: tuple[float, float] | None = None
        self._closed = False
        self.user_action_pending = False
        self._last_scale = settings.scale
        self._last_active = active_uptime_seconds()
        self._last_real = time.monotonic()
        self.now = 0.0
        self._timer: str | None = None
        self._event_timer: str | None = None
        self._events: deque[PlaybackEvent] = deque(maxlen=128)
        self.interaction = ObjectInteractionCoordinator(
            self.world, play=self._play, stop=self._stop,
            select_item=self._select_item, consume=self._consume,
            resolve_instance=self.awareness.instance_for_record,
            record_for_instance=self.awareness.record_for_instance,
            can_acquire=self._can_acquire, ground_x=self._ground_x,
            hand_type_conflicts=lambda record, instance: (
                held_type_conflicts_with_memory(
                    self.awareness.memory.get(record), instance,
                    self.world.snapshot(),
                )
            ),
            completed=self._completed,
            memory=self.awareness.memory, decide=self._decide,
            feedback=self._phase_feedback, cancel_feedback=cancel_feedback,
            now=lambda: self.now, inspection_seconds=BALANCE.number(
                "object_behavior", "inspection_seconds",
            ),
            withholding=self._withheld,
        )
        self._behavior = ObjectBehaviorCoordinator(
            state, self.awareness, self.interaction, self.world,
        )
        self._behavior.request_orientation()
        animated.on_playback = self._queue_event
        self.cursor = CursorItemGesture(
            root=root, world=self.world, view=self.view, settings=settings,
            track=track,
            ports=CursorItemPorts(
                capture_contact=self._capture_contact,
                handover=self.interaction.offer_on_release,
                assess_offer=self._assess_offer, present_offer=self._present_offer,
                known_instance=self.awareness.known_instance,
                cancel_feedback=self._cancel_offer, save=save,
                sync_view=self._sync_view,
                outside=lambda: feedback(GERMAN_TEXT.format("world.outside")),
                finished=self._behavior.request_orientation,
            ),
        )
        self._timer = root.after(33, self._frame)

    def memory_snapshot(self) -> ObjectMemorySnapshot:
        return self.awareness.memory.export(now=self.now)

    def save_snapshot(self) -> WorldSessionSnapshot:
        self._sync_geometry()
        return WorldSessionSnapshot(self.world.snapshot(), self.memory_snapshot(),
                                     self._body_x())

    def _surface(self) -> WorldSurface:
        track = self._track()
        return WorldSurface(
            max(1, track.right - track.left), max(1, track.ground_y),
            track.ground_inset(int(self.width), self.width * BALANCE.number(
                "object_behavior", "reach_widths")),
        )

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

    def _decide(self, token: str, context: ObjectUseContext) -> ObjectUseDecision:
        return self._behavior.decide(token, context)

    def _behavior_facts(self) -> BehaviorFacts:
        return BehaviorFacts(
            game_open=self._game_open(), controls_active=self._controls_active(),
            carrying=self.cursor.carrying,
            playback_busy=time.monotonic() < self._playback.until,
            user_action_pending=self.user_action_pending,
        )

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

    def _consume(
        self, key: str, token: str, memory_id: str, origin: ConsumptionOrigin,
    ) -> bool:
        outcome = self._consumption.commit(
            self.world, key, token, origin,
            self._inputs(time.time(), time.monotonic()),
            memory_id=memory_id,
        )
        if outcome.accepted:
            self._save()
            if origin == ConsumptionOrigin.HANDOVER:
                self._care = outcome.care
        return outcome.accepted

    def _withheld(self, key: str, loss: float) -> None:
        if self._relationship.withheld(
            key, loss, active_time=self.now, monotonic_time=time.monotonic(),
        ) > 0:
            self._save()

    def _select_item(self, item_id: str | None) -> None:
        overlay = self._animated.food_overlay
        if item_id is not None and self._contact is not None:
            overlay.contact_origin = self._contact
        else:
            overlay.contact_origin = None
        overlay.select(item_id)

    def _completed(self, token: str, consumed: bool) -> None:
        if not token:
            self._finish_sleep_care()
        self.awareness.intentions.complete(token, self.now, consumed=consumed)
        self._behavior.request_orientation()
        self._walk.movement.set_goal(None)
        self._visual.object_target = None
        self._contact = None
        self._care = None
        if token:
            self._save()

    def _finish_sleep_care(self) -> None:
        if self.time_progression.finish_sleep_care(self.state):
            self._save()

    def _ground_x(self, token: str) -> float:
        item = self.world.get(token)
        surface = self.world.snapshot().surface
        return surface.ground_x(self._body_x(), item.footprint)

    def _ground_approach(self, x: float) -> GroundApproach | None:
        track = self._track()
        return track.ground_approach(
            track.left + x, int(self.width),
            self.width * BALANCE.number("object_behavior", "reach_widths"),
        )

    def _can_acquire(self, token: str) -> bool:
        try:
            item = self.world.get(token)
        except WorldOperationError:
            return False
        if item.position is None:
            return False
        distance = abs(item.position.x - self._body_x())
        if item.state == ObjectState.USER_HELD:
            reachable = (
                distance <= self.width * .3
                and self.width * .05 <= item.position.height <= self.width * .9
            )
        else:
            track = self._track()
            reachable = track.can_grasp_ground(
                track.left + item.position.x, self.settings.x or 0, int(self.width),
                self.width * BALANCE.number("object_behavior", "reach_widths"),
            )
        return self._behavior.can_acquire(
            token, object_state=item.state, reachable=reachable,
            offer_ready=self.cursor.offer_ready, now=self.now,
            facts=self._behavior_facts(),
        )

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

    def _attention(self) -> ObjectAttention:
        """Sample before perception; translate native eyes to World coordinates."""
        pointer = self.root.winfo_pointerx(), self.root.winfo_pointery()
        attention = self._visual.attention(
            pointer, game_mode=self._game_open(),
            pointer_recent=time.monotonic()
            - self._mind.cursor_attention.last_pointer_move < 4.0,
        )
        track = self._track()
        return replace(attention, origin=(attention.origin[0] - track.left,
                                         attention.origin[1] + track.ground_y))

    def orientation_side(self) -> LookSide | None:
        return self._behavior.orientation_side

    def update(self, _now: float) -> None:
        if self._closed:
            return
        episode = self.state.sleep_episode
        if episode.care_break:
            finishing = sleep_care_complete(
                episode, satiety=self.state.satiety, elapsed=self.state.lived_seconds,
            )
            if finishing:
                if self.interaction.active:
                    self.interaction.interrupt(self._finish_sleep_care)
                else:
                    self._finish_sleep_care()
            elif (not self.interaction.active and self.state.satiety <= 0
                    and not ObjectConsumption.remembered_stock(
                        self.world, self.awareness.memory,
                    )):
                self.interaction.start_food_search()
        elif self.state.sleeping and self.interaction.active:
            self.interaction.interrupt(lambda: None)
        self.interaction.update()
        snapshot = self.world.snapshot()
        if self.cursor.carrying and not self.cursor.inside:
            snapshot = replace(snapshot, objects=tuple(
                item for item in snapshot.objects
                if item.instance_id != self.cursor.instance_id
            ))
        observation = self._behavior.observe(
            snapshot, now=self.now, x=self._body_x(), width=self.width,
            facts=self._behavior_facts(), attention=self._attention(),
            presentation=self.cursor.presentation(
                self._animated.cursor_eye_position, self.width,
            ),
        )
        gaze = observation.gaze
        if observation.absence_noticed:
            self._walk.movement.set_goal(None)
            self.cursor.offer_ready = False
        self._visual.object_target = (
            (self._track().left + gaze.x, self._track().ground_y - gaze.height)
            if gaze is not None else None
        )
        if observation.absence_noticed:
            self._save()
            return
        if observation.observe_offer:
            self.cursor.observe_offer()
        else:
            self.cursor.offer_ready = False
        track = self._track()
        motion = self._behavior.advance(
            observation.goal, blocked=observation.blocked,
            search_position=SearchPosition(
                self.width / 2,
                max(self.width / 2, track.right - track.left - self.width / 2),
                self._body_x(),
            ),
        )
        if isinstance(motion, SearchMotion):
            self._show_search(motion)
            return
        if isinstance(motion, Hold):
            self._walk.movement.set_goal(None)
            return
        goal = motion.target
        approach = self._ground_approach(goal.x)
        if approach is None:
            self._walk.movement.set_goal(None)
            self._behavior.unreachable(now=self.now)
            return
        self._walk.movement.set_goal(approach.standing_x)
        if not approach.arrived(self.settings.x or 0):
            return
        instance = self.awareness.instance_for_record(goal.token)
        if instance is not None and self._can_acquire(instance):
            self._walk.movement.set_goal(None)
            self._capture_contact(instance)
            self.interaction.arrive()
        elif (instance is not None
              and self.world.get(instance).state == ObjectState.RESTING):
            # Native motion may still be settling inside the two-pixel
            # arrival tolerance; retain the exact standing goal for reach.
            return
        else:
            # A failed local reach is not evidence that the place is empty.
            # Stop the approach and let the normal timed absence perception
            # establish the loss before announcing or beginning a search.
            self._walk.movement.set_goal(None)

    def _show_search(self, search: SearchMotion) -> None:
        track = self._track()
        direction = -1 if search.center < self._body_x() else 1
        base = track.clamp_x(track.left + search.center - self.width / 2,
                             int(self.width))
        self._walk.movement.set_goal(base)
        self._visual.object_target = (
            base + self.width / 2 + (direction or 1) * self.width,
            track.ground_y - self.width * .15,
        )

    def request_contact(self, action: Callable[[], None]) -> None:
        """Ordinary input respects commitment; explicit commands use interrupt."""
        if not self.interaction.acknowledge_contact():
            self.interrupt(action)

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
        self._sync_geometry()

        def begin() -> None:
            self._behavior.request_orientation()
            self.cursor.begin(item_id)

        self._request_gesture(begin)

    def _request_gesture(self, action: Callable[[], None]) -> None:
        if self.interaction.active:
            action()
            return
        dispatching = True

        def start() -> None:
            # A queued put-down can outlive the physical press which requested it.
            buttons = mouse_buttons_down_windows()
            if not dispatching and buttons is not None and not buttons[0]:
                return
            action()

        self.interrupt(start)
        dispatching = False

    def _cancel_offer(self) -> None:
        if not self.interaction.active:
            self._cancel_feedback()

    def begin_relocate(self, token: str, revision: int) -> None:
        self._sync_geometry()
        item = self.world.get(token)
        if (self.cursor.carrying or item.state != ObjectState.RESTING
                or item.revision != revision):
            return
        assert item.position is not None
        previous_position = (item.position.x, item.position.height)
        attention = self._attention()

        def acquire() -> None:
            if self.cursor.begin_existing(token, revision):
                record = self.awareness.witness_take(
                    token, position=previous_position, now=self.now,
                    attention=attention,
                    committed=self.interaction.focus_record,
                )
                self._behavior.request_orientation()
                if record is not None and self.interaction.target_taken(record):
                    self._walk.movement.set_goal(None)

        self._request_gesture(acquire)

    def _assess_offer(self, token: str) -> ObjectUseDecision | None:
        return self._behavior.assess_offer(token, facts=self._behavior_facts())

    def _present_offer(self, cue: ObjectFeedback) -> None:
        if self.interaction.active:
            return
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
        self._sync_geometry()
        self.world.advance_motion(elapsed, self._motion_parameters)
        self.cursor.update()
        self._sync_view()
        self._timer = self.root.after(33, self._frame)

    def _sync_geometry(self) -> None:
        self.world.change_surface(self._surface())
        if self._last_scale != self.settings.scale:
            self._refresh_footprints()
            self._last_scale = self.settings.scale

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
