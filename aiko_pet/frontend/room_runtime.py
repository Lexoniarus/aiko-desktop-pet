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
from ..infrastructure.world_motion import motion_parameters
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
from .room_drag import RoomDrag
from .room_leisure import RoomLeisure
from .room_locomotion import RoomLocomotion
from .room_playback import RoomPlayback
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
        self.leisure = RoomLeisure(mind.rng, rest_cycle=playback.rest_cycle)
        self.facing = 1
        self.held_item: str | None = None
        self.held_pose = "closed_world"
        self._called: RoomPoint | None = None
        self._wander: RoomPoint | None = None
        self._offered: tuple[str, float, str] | None = None
        self._dragged: RoomDrag | None = None
        self._gesture_serial = 0
        self._motion_parameters = motion_parameters()
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
        safe_depths = tuple(
            (key, RoomGeometry.accessible(RoomPoint(0, depth)).depth)
            for key, depth in self.spatial.object_depths
        )
        world.locate_in_room(
            replace(self.spatial, pet=safe_position, object_depths=safe_depths)
        )

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

    @property
    def drag_ready(self) -> bool:
        return bool(self._dragged and self._dragged.ready)

    @property
    def drag_instance(self) -> str | None:
        return self._dragged.instance if self._dragged else None

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
        item = self.world.get(instance)
        if item.position is None:
            return False
        point = RoomPoint(item.position.x % 5100, self.spatial.depth_for(instance))
        return self.behavior.can_acquire(
            instance,
            object_state=item.state,
            reachable=(
                RoomGeometry.distance(self.position, point)
                <= (
                    150
                    if item.state == ObjectState.USER_HELD
                    else RoomGeometry.ground_reach
                )
                and (
                    item.state != ObjectState.USER_HELD
                    or 15 <= item.position.height <= 450
                )
            ),
            offer_ready=self._dragged.ready if self._dragged else True,
            now=self.now,
            facts=BehaviorFacts(game_open=self.game_open()),
        )

    def call(self, point: RoomPoint) -> None:
        if self.state.sleeping:
            raise ValueError("Aiko schläft gerade.")

        def start() -> None:
            self.pause_route()
            self._called = RoomGeometry.accessible(point)

        self.interaction.interrupt(start)
        self.awareness.intentions.cancel(self.now)

    def pause_route(self) -> None:
        self._called = self._wander = None
        self.moving = False
        self.leisure.suspend(self.now, cancel_outing=True)

    def place(self, definition: str, point: RoomPoint) -> str:
        point = RoomGeometry.accessible(point)
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
        point = RoomGeometry.accessible(point)
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
        position = WorldPosition(x, 240)
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
            instance, WorldPosition(x, 240), expected_revision=item.revision
        )
        self._depth(instance, self.position.depth)
        self._offered = instance, self.now, f"offer_{instance}_{item.revision}"

    def begin_drag(
        self,
        instance: str | None = None,
        revision: int = 0,
        *,
        definition: str | None = None,
    ) -> None:
        if self._dragged is not None or self._offered is not None:
            raise ValueError("Ein Gegenstand wird bereits gehalten.")
        self.pause_route()

        if instance is None:
            if definition is None:
                raise ValueError("Kein Gegenstand ausgewählt.")
            item = self.world.create_held(
                definition,
                WorldPosition(self.position.x, 0),
                ObjectFootprint(24, 24),
            )
            original, depth = None, self.position.depth
            self._depth(item.instance_id, depth)
        else:
            item = self.world.get(instance)
            if item.position is None:
                raise ValueError("Dieser Gegenstand liegt nicht im Zimmer.")
            original, depth = item.position, self.spatial.depth_for(instance)
            self.world.take_resting(instance, expected_revision=revision)
            record = self.awareness.witness_take(
                instance,
                position=(original.x, original.height),
                now=self.now,
                attention=ObjectAttention(
                    "survey", (self.facing, 0), (self.position.x, 240), 490
                ),
                committed=self.interaction.focus_record,
            )
            if record is not None:
                self.interaction.target_taken(record)
        self._gesture_serial += 1
        self._dragged = RoomDrag(
            item.instance_id, original, depth, f"room_drag_{self._gesture_serial}"
        )
        self.behavior.refresh_after_placement()

    def move_drag(
        self,
        point: RoomPoint,
        height: float,
        *,
        inside: bool,
        face: tuple[float, float] | None = None,
    ) -> None:
        drag = self._dragged
        if drag is None:
            raise ValueError("Kein Gegenstand wird gezogen.")
        item = self.world.get(drag.instance)
        surface = self.world.snapshot().surface
        point = RoomGeometry.accessible(point)
        self.world.move_held(
            drag.instance,
            WorldPosition(surface.ground_x(point.x, item.footprint), height),
            expected_revision=item.revision,
        )
        self._depth(drag.instance, point.depth)
        drag.inside = inside
        drag.presentation = (
            ItemPresentation(drag.gesture, *face) if inside and face else None
        )

    def cancel_drag(self) -> None:
        if self._dragged is None:
            return
        drag = self._dragged
        item = self.world.get(drag.instance)
        if drag.original is None:
            self.world.remove(drag.instance, expected_revision=item.revision)
        else:
            self.world.return_user_held(
                drag.instance, drag.original.x, expected_revision=item.revision
            )
            self._depth(drag.instance, drag.depth)
        self._dragged = None
        self.behavior.refresh_after_placement()

    def drop_drag(self, point: RoomPoint, *, offer: bool, height: float = 0) -> None:
        if self._dragged is None:
            raise ValueError("Kein Gegenstand wird gezogen.")
        point = RoomGeometry.accessible(point)
        instance = self._dragged.instance
        item = self.world.get(instance)
        destination = point
        x = self.world.snapshot().surface.ground_x(destination.x, item.footprint)
        item = self.world.move_held(
            instance,
            WorldPosition(x, height),
            expected_revision=item.revision,
        )
        self._depth(instance, destination.depth)
        accepted = offer and self.interaction.offer_on_release(instance)
        if not accepted:
            self.world.release(instance, expected_revision=item.revision)
        self._dragged = None
        self.behavior.refresh_after_placement()

    def update(self, seconds: float) -> None:
        self.now += seconds
        self.moving = False
        self.world.advance_motion(seconds, self._motion_parameters)
        self.interaction.update()
        target = self.awareness.intentions.goal
        focused = self.awareness.memory.get(self.interaction.focus_record or "")
        point = focused or target
        side = self.behavior.orientation_side if not self.interaction.active else None
        direction = (
            (side, 0.0)
            if side is not None
            else (
                ((point.x - self.position.x) / 490, (point.height - 240) / 490)
                if point is not None
                else self.locomotion.gaze or (self.facing, -0.1)
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
            mode,
            direction,
            (self.position.x, 240),
            490,
            focused_place=point is not None,
        )
        presentation = None
        if self._offered is not None and self.behavior.orientation_side is None:
            instance, started, gesture = self._offered
            presentation = instance, ItemPresentation(gesture, 0, 0)
            attention = ObjectAttention("cursor", (0, 0), (self.position.x, 240), 490)
        drag = self._dragged
        if drag is not None and drag.presentation is not None and side is None:
            presentation = drag.instance, drag.presentation
            direction = (drag.presentation.x, -drag.presentation.y)
            attention = ObjectAttention(
                "cursor", direction, (self.position.x, 240), 490
            )
        previewing = drag is not None and self.playback.player.subject == drag.gesture
        facts = BehaviorFacts(
            game_open=self.game_open(),
            carrying=drag is not None,
            playback_busy=self.playback.player.active and not previewing,
        )
        observation = self.behavior.observe(
            self.world.snapshot(),
            now=self.now,
            x=self.position.x,
            width=490,
            presentation=presentation,
            attention=attention,
            facts=facts,
        )
        if drag is not None:
            decision = (
                self.behavior.assess_offer(drag.instance, facts=facts)
                if observation.observe_offer and drag.inside
                else None
            )
            item = self.world.get(drag.instance)
            near = (
                item.position is not None
                and RoomGeometry.distance(
                    self.position,
                    RoomPoint(item.position.x, self.spatial.depth_for(drag.instance)),
                )
                < 110
                and abs(item.position.height - 100) < 65
            )
            drag.ready = bool(decision and decision.use and near)
            record = self.awareness.record_for_instance(drag.instance)
            if decision is not None and record is not None:
                cue = record, decision.use
                if drag.feedback != cue and not self.interaction.active:
                    drag.feedback = cue
                    known = self.awareness.memory.get(record)
                    reaction = self.mind.select_reaction(
                        "object_offer" if decision.use else "object_refuse",
                        self.state,
                        context_at(time.time()),
                        self.now,
                    )
                    self.playback.speak(
                        format_object_reaction(
                            reaction, known.identity if known else None, self.items
                        )
                        if reaction
                        else None,
                        subject=drag.gesture,
                        animate=False,
                        require_presentation=False,
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
        if (
            not self.interaction.active
            and not self.playback.player.active
            and self.playback.animation == "idle"
        ):
            destination = self._called or destination
            if (
                destination is None
                and self.wandering()
                and self._wander is None
                and self._called is None
            ):
                self._wander = self.leisure.destination(self.now, self.position)
            destination = destination or (
                self._wander if self.wandering() or self.night() else None
            )
        if (
            destination is None
            or self._offered is not None
            or self._dragged is not None
            or self.game_open()
            or self.state.sleeping
            or self.state.energy < 15
            or self.playback.animation != "idle"
        ):
            has_focus = bool(drag or side is not None or point is not None)
            if (
                not has_focus
                and not self.interaction.active
                and not self.playback.player.active
                and self.playback.animation == "idle"
                and not self.game_open()
                and not self.state.sleeping
            ):
                self.leisure.pose(self.now, self.state, self.locomotion)
            else:
                self.leisure.suspend(self.now)
                self.locomotion.rest(
                    self.now,
                    (direction[0], -direction[1]) if has_focus else None,
                )
            return
        self.leisure.suspend(self.now)
        previous = self.position
        route = RoomGeometry.route(previous, RoomGeometry.accessible(destination))
        if not self.locomotion.walk(self.now, previous, route[0]):
            return
        current = RoomGeometry.approach(
            previous,
            destination,
            min(seconds, 0.5),
            speed=self.locomotion.speed,
        )
        self.moving = current != previous
        if self.moving:
            self.facing = 1 if RoomGeometry.delta(previous.x, current.x) >= 0 else -1
            self.world.locate_in_room(replace(self.spatial, pet=current))
        if RoomGeometry.distance(current, RoomGeometry.accessible(destination)) < 1:
            if self._wander is not None and not self.night():
                self.leisure.arrived(self.now, self.facing)
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
        self.pause_route()
