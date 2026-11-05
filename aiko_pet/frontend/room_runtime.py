"""Room environment adapter for existing object perception and interaction."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace

from ..application.active_time import ActiveSessionClock, SessionInputs, TimeProgression
from ..application.object_awareness import (
    ObjectAwareness,
    held_type_conflicts_with_memory,
)
from ..application.object_behavior import (
    Approach,
    BehaviorFacts,
    ObjectBehaviorCoordinator,
    SearchMotion,
)
from ..application.object_consumption import ObjectConsumption
from ..application.object_feedback import FeedbackReceipt, ObjectFeedback
from ..application.object_interaction import ObjectInteractionCoordinator
from ..application.object_interaction_state import SearchPosition
from ..application.session_time import SessionTimeProgression
from ..pet.animation.item_assets import ItemCatalog
from ..pet.balance import BALANCE
from ..pet.consumption import ConsumptionOrigin
from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.object_attention import AttentionMode, ObjectAttention
from ..pet.mind.object_knowledge import ObjectMemorySnapshot
from ..pet.mind.object_perception import ItemPresentation
from ..pet.routine import context_at
from ..pet.state import PetState
from ..world.contracts import ObjectFootprint, ObjectState, WorldPosition
from ..world.room import RoomGeometry, RoomPoint, RoomSpatialState
from ..world.state import WorldState
from .room_playback import RoomPlayback
from .room_locomotion import RoomLocomotion
from .view_models.object_reactions import format_object_reaction


class RoomRuntime:
    """Map spatial reach and movement onto the one existing interaction owner."""

    def __init__(
        self,
        world: WorldState,
        state: PetState,
        mind: PetMind,
        routine: AdaptiveRoutine,
        clock: ActiveSessionClock,
        playback: RoomPlayback,
        *,
        memory: ObjectMemorySnapshot | None,
        inputs: Callable[[], SessionInputs],
        game_open: Callable[[], bool],
        items: ItemCatalog,
        night: Callable[[], bool],
        wandering: Callable[[], bool],
        time_progression: Callable[[SessionTimeProgression], TimeProgression],
    ) -> None:
        self.world, self.state, self.mind = world, state, mind
        self.playback, self.inputs, self.game_open = playback, inputs, game_open
        self.items, self.night = items, night
        self.wandering = wandering
        self.awareness = ObjectAwareness(memory)
        self.awareness.reconcile_books(world.snapshot())
        self.progression = SessionTimeProgression(world, self.awareness.memory)
        admitted_time = time_progression(self.progression)
        self.consumption = ObjectConsumption(
            state,
            mind,
            routine,
            clock=clock,
            progression=admitted_time,
            memory=self.awareness.memory,
        )
        self.now = 0.0
        self.moving = False
        self.locomotion = RoomLocomotion()
        self.facing = 1
        self.held_item: str | None = None
        self.held_pose = "closed_world"
        self._called: RoomPoint | None = None
        self._wander: RoomPoint | None = None
        self._next_wander = 10.0
        self._offered: tuple[str, float, str] | None = None
        self._dragged: tuple[str, WorldPosition, float] | None = None
        self.interaction = ObjectInteractionCoordinator(
            world,
            play=playback.play_animation,
            stop=playback.stop_animation,
            select_item=self._select_item,
            consume=self._consume,
            resolve_instance=self.awareness.instance_for_record,
            record_for_instance=self.awareness.record_for_instance,
            can_acquire=self._can_acquire,
            ground_x=lambda _item: self.position.x,
            hand_type_conflicts=lambda record,
            instance: held_type_conflicts_with_memory(
                self.awareness.memory.get(record),
                instance,
                world.snapshot(),
            ),
            completed=self._completed,
            memory=self.awareness.memory,
            decide=lambda record, context: self.behavior.decide(record, context),
            feedback=self._feedback,
            cancel_feedback=playback.player.cancel,
            now=lambda: self.now,
            inspection_seconds=BALANCE.number("object_behavior", "inspection_seconds"),
            experience=state.experience_interaction,
            begin_handover=lambda item, record: self.consumption.begin_handover(
                world,
                item,
                inputs(),
                memory_id=record,
            ),
            acknowledge_handover=lambda item,
            record: self.consumption.acknowledge_handover(
                world,
                item,
                inputs(),
                memory_id=record,
            ),
            finish_handover=lambda item: self.consumption.finish_handover(world, item),
        )
        self.behavior = ObjectBehaviorCoordinator(
            state, self.awareness, self.interaction, world
        )
        self.behavior.request_orientation()
        playback.receive = self.interaction.receive
        if world.snapshot().room is None:
            world.locate_in_room(RoomSpatialState())
        safe_position = RoomGeometry.accessible(self.position)
        if safe_position != self.position:
            world.locate_in_room(replace(self.spatial, pet=safe_position))

    @property
    def spatial(self) -> RoomSpatialState:
        room = self.world.snapshot().room
        assert room is not None
        return room

    @property
    def position(self) -> RoomPoint:
        return self.spatial.pet

    def _select_item(self, item: str | None) -> None:
        self.held_item = item

    def _completed(self, record: str, consumed: bool) -> None:
        self.awareness.intentions.complete(record, self.now, consumed=consumed)
        self.behavior.request_orientation()
        self.playback.stop_animation()

    def _consume(
        self, key: str, item: str, record: str, origin: ConsumptionOrigin
    ) -> bool:
        return self.consumption.commit(
            self.world,
            key,
            item,
            origin,
            self.inputs(),
            memory_id=record,
        ).accepted

    def _feedback(self, cue: ObjectFeedback) -> None:
        reaction = self.mind.select_reaction(
            cue.event, self.state, context_at(time.time()), self.now
        )
        self.playback.speak(
            format_object_reaction(reaction, cue.identity, self.items)
            if reaction
            else None,
            subject=cue.record_id,
            animate=False,
            require_presentation=False,
            completed=lambda done: self.interaction.receive_feedback(
                FeedbackReceipt(cue.key, done),
            ),
        )

    def _can_acquire(self, instance: str) -> bool:
        if self._dragged is not None and self._dragged[0] == instance:
            return False
        item = self.world.get(instance)
        if item.position is None:
            return False
        point = RoomPoint(item.position.x % 5100, self.spatial.depth_for(instance))
        return self.behavior.can_acquire(
            instance,
            object_state=item.state,
            reachable=RoomGeometry.distance(self.position, point) <= 180,
            offer_ready=True,
            now=self.now,
            facts=BehaviorFacts(game_open=self.game_open()),
        )

    def call(self, point: RoomPoint) -> None:
        if self.state.sleeping:
            raise ValueError("Aiko schläft gerade.")
        self.interaction.interrupt(
            lambda: setattr(self, "_called", RoomGeometry.accessible(point))
        )
        self.awareness.intentions.cancel(self.now)

    def pause_route(self) -> None:
        self._called = self._wander = None
        self.moving = False

    def place(self, definition: str, point: RoomPoint) -> str:
        if RoomGeometry.accessible(point) != point:
            raise ValueError("Bitte die Portion auf dem freien Boden ablegen.")
        footprint = ObjectFootprint(24, 24)
        x = self.world.snapshot().surface.ground_x(point.x, footprint)
        item = self.world.place_resting(definition, x, footprint)
        self._depth(item.instance_id, point.depth)
        self.behavior.refresh_after_placement()
        return item.instance_id

    def _depth(self, instance: str, depth: float) -> None:
        depths = dict(self.spatial.object_depths)
        depths[instance] = depth
        self.world.locate_in_room(
            replace(self.spatial, object_depths=tuple(depths.items()))
        )

    def relocate(self, instance: str, revision: int, point: RoomPoint) -> None:
        if RoomGeometry.accessible(point) != point:
            raise ValueError("Bitte den Gegenstand auf dem freien Boden ablegen.")
        item = self.world.get(instance)
        if item.state != ObjectState.RESTING:
            raise ValueError("Dieser Gegenstand wird gerade benutzt.")
        x = self.world.snapshot().surface.ground_x(point.x, item.footprint)
        self.world.move_resting(instance, x, expected_revision=revision)
        self._depth(instance, point.depth)
        self.behavior.refresh_after_placement()

    def offer(self, definition: str) -> None:
        if (
            self._offered is not None
            or self._dragged is not None
            or self.game_open()
            or self.state.sleeping
        ):
            raise ValueError("Aiko kann gerade nichts entgegennehmen.")
        self.pause_route()
        x = self.world.snapshot().surface.ground_x(
            self.position.x, ObjectFootprint(24, 24)
        )
        position = WorldPosition(x, 80)
        item = self.world.create_held(definition, position, ObjectFootprint(24, 24))
        self._depth(item.instance_id, self.position.depth)
        self._offered = item.instance_id, self.now, f"offer_{item.instance_id}"

    def offer_existing(self, instance: str, revision: int) -> None:
        if (
            self._offered is not None
            or self._dragged is not None
            or self.game_open()
            or self.state.sleeping
        ):
            raise ValueError("Aiko kann gerade nichts entgegennehmen.")
        self.pause_route()
        item = self.world.take_resting(instance, expected_revision=revision)
        x = self.world.snapshot().surface.ground_x(self.position.x, item.footprint)
        item = self.world.move_held(
            instance, WorldPosition(x, 80), expected_revision=item.revision
        )
        self._depth(instance, self.position.depth)
        self._offered = instance, self.now, f"offer_{instance}_{item.revision}"

    def begin_drag(self, instance: str, revision: int) -> None:
        if self._dragged is not None or self._offered is not None:
            raise ValueError("Ein Gegenstand wird bereits gehalten.")

        item = self.world.get(instance)
        if item.position is None:
            raise ValueError("Dieser Gegenstand liegt nicht im Zimmer.")
        original = item.position
        self.world.take_resting(instance, expected_revision=revision)
        self._dragged = instance, original, self.spatial.depth_for(instance)
        if self.interaction.instance_id == instance:
            self.interaction.interrupt(lambda: None)
        self.behavior.refresh_after_placement()

    def cancel_drag(self) -> None:
        if self._dragged is None:
            return
        instance, position, depth = self._dragged
        item = self.world.get(instance)
        self.world.return_user_held(
            instance, position.x, expected_revision=item.revision
        )
        self._depth(instance, depth)
        self._dragged = None
        self.behavior.refresh_after_placement()

    def drop_drag(self, point: RoomPoint, *, offer: bool) -> None:
        if self._dragged is None:
            raise ValueError("Kein Gegenstand wird gezogen.")
        if offer and (
            self._offered is not None or self.game_open() or self.state.sleeping
        ):
            raise ValueError("Aiko kann gerade nichts entgegennehmen.")
        if not offer and RoomGeometry.accessible(point) != point:
            raise ValueError("Bitte den Gegenstand auf dem freien Boden ablegen.")
        instance = self._dragged[0]
        item = self.world.get(instance)
        destination = self.position if offer else point
        x = self.world.snapshot().surface.ground_x(destination.x, item.footprint)
        item = self.world.move_held(
            instance,
            WorldPosition(x, 80 if offer else 0),
            expected_revision=item.revision,
        )
        self._depth(instance, destination.depth)
        if offer:
            self.pause_route()
            self._offered = instance, self.now, f"offer_{instance}_{item.revision}"
        else:
            self.world.release(instance, expected_revision=item.revision)
            item = self.world.get(instance)
            self.world.land(instance, expected_revision=item.revision)
            self.behavior.refresh_after_placement()
        self._dragged = None

    def update(self, seconds: float) -> None:
        self.now += seconds
        self.moving = False
        self.interaction.update()
        target = self.awareness.intentions.goal
        focused = self.awareness.memory.get(self.interaction.focus_record or "")
        point = focused or target
        side = self.behavior.orientation_side if not self.interaction.active else None
        direction = (
            (side, 0.0)
            if side is not None
            else (
                ((point.x - self.position.x) / 192, (point.height - 80) / 192)
                if point is not None
                else (self.facing, -0.1)
            )
        )
        mode: AttentionMode = (
            "object"
            if self.interaction.active and not self.interaction.searching
            else "survey"
        )
        if side is not None and not self.interaction.active:
            mode = "survey"
        attention = ObjectAttention(
            mode, direction, (self.position.x, 80), 192, focused_place=point is not None
        )
        presentation = None
        if self._offered is not None and self.behavior.orientation_side is None:
            instance, started, gesture = self._offered
            presentation = instance, ItemPresentation(gesture, 0, 0)
            attention = ObjectAttention("cursor", (0, 0), (self.position.x, 80), 192)
        observation = self.behavior.observe(
            self.world.snapshot(),
            now=self.now,
            x=self.position.x,
            width=192,
            presentation=presentation,
            attention=attention,
            facts=BehaviorFacts(
                game_open=self.game_open(), playback_busy=self.playback.player.active
            ),
        )
        for seen in self.awareness.observations:
            observed_instance = self.awareness.instance_for_record(seen.token)
            if observed_instance is not None and attention.sees(seen.x, seen.height):
                self.awareness.memory.observe_depth(
                    seen.token, self.spatial.depth_for(observed_instance)
                )
        if self._offered is not None:
            instance, started, _gesture = self._offered
            if self.now - started >= 1.5:
                if self.interaction.offer_on_release(instance):
                    self._offered = None
                elif self.now - started > 8:
                    item = self.world.get(instance)
                    self.world.release(instance, expected_revision=item.revision)
                    item = self.world.get(instance)
                    self.world.land(instance, expected_revision=item.revision)
                    self._offered = None
        motion = self.behavior.advance(
            observation.goal,
            blocked=observation.blocked,
            search_position=SearchPosition(96, 5004, self.position.x),
        )
        destination = None
        if (
            self.night()
            and not self.state.sleeping
            and not self.interaction.active
            and self.state.lived_seconds >= self.state.sleep_episode.protect_until
        ):
            self._wander = RoomGeometry.accessible(RoomGeometry.anchors[-1].position)
            self._next_wander = self.now + 3600
        if isinstance(motion, SearchMotion):
            destination = RoomPoint(motion.center % 5100, 0.9)
        elif isinstance(motion, Approach):
            focused_instance = self.awareness.instance_for_record(motion.target.token)
            known = self.awareness.memory.get(motion.target.token)
            destination = RoomPoint(
                motion.target.x % 5100, known.depth if known else 0.9
            )
            if focused_instance is not None and self._can_acquire(focused_instance):
                self.interaction.arrive()
                destination = None
        if not self.interaction.active and not self.playback.player.active:
            destination = self._called or destination
            if (
                destination is None
                and self.wandering()
                and self.now >= self._next_wander
            ):
                self._wander = RoomGeometry.accessible(
                    self.mind.rng.choice(RoomGeometry.anchors).position
                )
                self._next_wander = self.now + self.mind.rng.uniform(20, 55)
            destination = destination or (
                self._wander if self.wandering() or self.night() else None
            )
        if (
            destination is None
            or self._offered is not None
            or self.game_open()
            or self.state.sleeping
            or self.state.energy < 15
        ):
            self.locomotion.rest(self.now)
            return
        previous = self.position
        route = RoomGeometry.route(previous, RoomGeometry.accessible(destination))
        if not self.locomotion.walk(self.now, previous, route[0]):
            return
        current = RoomGeometry.approach(
            previous, destination, min(seconds, 0.5), speed=self.locomotion.speed,
        )
        self.moving = current != previous
        if self.moving:
            self.facing = 1 if RoomGeometry.delta(previous.x, current.x) >= 0 else -1
            self.world.locate_in_room(replace(self.spatial, pet=current))
        if RoomGeometry.distance(current, RoomGeometry.accessible(destination)) < 1:
            self._called = self._wander = None

    def suspend(self) -> None:
        self.cancel_drag()
        self.interaction.suspend()
        if self._offered is not None:
            item = self.world.get(self._offered[0])
            if item.state == ObjectState.USER_HELD:
                item = self.world.release(
                    item.instance_id, expected_revision=item.revision
                )
                self.world.land(item.instance_id, expected_revision=item.revision)
            self._offered = None
        self._called = self._wander = None
        self.moving = False
