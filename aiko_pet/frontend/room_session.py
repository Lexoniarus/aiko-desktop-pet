"""One portable Tamagotchi session composed from the existing rule owners."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import Any

from ..application.active_time import ActiveSessionClock, SessionInputs
from ..application.commands import CareCommand
from ..application.contact import (
    ContactCoordinator,
    ContactPorts,
    acknowledge_interaction_text,
)
from ..application.controller import CareController
from ..application.game_experience import GameExperienceCoordinator
from ..application.read_snapshot import snapshot_pet
from ..application.room_contracts import json_value
from ..application.room_routine import RoomRoutine
from ..application.router import ApplicationRouter
from ..application.session import LoadedPetData, SavedPetStore
from ..application.session_time import SessionTimeProgression
from ..application.settings import PetSettings
from ..application.wish_context import wish_context_for
from ..application.wish_forecast import RoomTimeProgression, WishForecastService
from ..infrastructure.room_layout import load_room_layout
from ..pet.animation.character import CharacterCatalog
from ..pet.animation.expression import EXPRESSION_CLIPS
from ..pet.animation.item_assets import ItemCatalog
from ..pet.care_result import CareEffect
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.interaction_events import SocialCompletion
from ..pet.mind import PetMind
from ..pet.mind.catalog import Reaction
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.routine import context_at
from ..pet.wish_catalog import WISH_CATALOG
from ..pet.wishes import wish_to_express
from ..telemetry import ComputerSnapshot
from ..world.contracts import WorldSurface
from ..world.room import RoomPoint
from ..world.state import WorldState
from .games.session import GameSessionCoordinator
from .room_content import RoomContent
from .room_playback import RoomPlayback
from .room_runtime import RoomRuntime
from .view_models.care_text import care_animation, format_care_response
from .view_models.emotional_text import (
    MOODLET_ICONS,
    moodlet_description,
    wish_description,
)
from .view_models.projections import project_status


class RoomSession:
    """No duplicate pet values, clock, inventory, dialogue or reward rules."""

    def __init__(
        self,
        store: SavedPetStore,
        loaded: LoadedPetData,
        mind: PetMind,
        world: WorldState,
        animations: CharacterCatalog,
        items: ItemCatalog,
    ) -> None:
        self.store, self.state, self.settings = store, loaded.state, loaded.settings
        self.mind = mind
        self.settings.observe_computer = self.settings.learn_rhythm = False
        self.settings.follow_cursor = False
        self.routine = RoomRoutine(loaded.adaptive_memory)
        self.clock = ActiveSessionClock(lambda: None, wall_time=time.time)
        self.revision = loaded.revision
        self.social_history = loaded.social_history
        self.horoscope_history = loaded.horoscope
        self.error: str | None = None
        self.content: RoomContent | None = None
        self.game_snapshot: dict[str, Any] | None = None
        self._preparing_game: str | None = None
        self._suspended = False
        self._last_tick = time.time()
        self._last_saved = self._last_tick
        self._next_comment = time.monotonic() + 35
        self.playback = RoomPlayback(
            animations,
            social_completed=self._social_completed,
            mark_spoken=lambda: self.mind.record_care_contact(time.monotonic()),
            text_presented=lambda event: acknowledge_interaction_text(
                self.state, event
            ),
            wish_presented=self.state.note_wish_expression,
        )
        if loaded.world is not None:
            world.restore_snapshot(loaded.world)
        layout = load_room_layout()
        world.change_surface(
            WorldSurface(layout.width, layout.wall_height + 25, 6), recovering=True,
        )
        self.room = RoomRuntime(
            world,
            self.state,
            mind,
            self.routine,
            self.clock,
            self.playback,
            memory=loaded.object_memory,
            inputs=self.inputs,
            game_open=lambda: self.game_snapshot is not None,
            items=items,
            night=lambda: (
                self.settings.auto_routine
                and self.routine.sleep_context().window(time.time())[0]
            ),
            wandering=lambda: self.settings.auto_walk,
            time_progression=self._make_progression,
        )
        self.playback.can_express = lambda: (
            not self.room.moving
            and not self.state.sleeping
            and self.playback.animation == "idle"
        )
        self.router = ApplicationRouter(
            CareController(
                self.state,
                mind,
                self.routine,
                clock=self.clock,
                progression=self.progression,
            ),
            game_experience=GameExperienceCoordinator(
                self.state,
                mind,
                self.routine,
                clock=self.clock,
                progression=self.progression,
                arrangement_ready=lambda: not self.room.interaction.search_active,
            ),
        )
        self.games = GameSessionCoordinator(
            self.router, self.state, mind, self.playback, self.inputs
        )
        self.contact = ContactCoordinator(
            state=self.state,
            mind=mind,
            adaptive=self.routine,
            ports=ContactPorts(
                context=lambda: context_at(time.time()),
                mark_hover=lambda _now: None,
                interrupt_walk=self.room.pause_route,
                show_toolbar=lambda: None,
                game_open=lambda: self.games.sequence is not None,
                cancel_followup=self.playback.player.cancel,
                hide_speech=self.playback.player.cancel,
                react=lambda reaction, _duration: self.playback.speak(reaction),
                should_greet=lambda _now: True,
                story_active=lambda: self.playback.player.story_active,
                advance_story=self.playback.advance_story,
                foreground_active=lambda: self.room.interaction.active,
                playback_active=lambda: self.playback.player.active,
                interruptible_playback=lambda: self.playback.player.interruptible,
                reaction_event=lambda: self.playback.player.event,
                advance_time=lambda: self.router.advance_time(self.inputs()),
                wake_from_clicks=self._wake_from_clicks,
            ),
        )
        if loaded.restored_from_save:
            self.progression.advance(
                self.state,
                self.inputs(),
                max(0, time.time() - self.state.updated_at),
                reconstruct=True,
            )
        self.state.anchor_live_session(time.time())
        self.clock.consume(wall_time=time.time())

    def wish_context(self, state: Any = None) -> Any:
        return wish_context_for(
            self.state if state is None else state,
            online_social=self.settings.online_social,
            prepared_social=self.content.runtime.prepared_categories
            if self.content
            else frozenset(),
        )

    def _make_progression(self, base: SessionTimeProgression) -> RoomTimeProgression:
        self.progression = RoomTimeProgression(base, self.wish_context)
        return self.progression

    def forecast(self) -> Any:
        return WishForecastService().plan(
            self.state,
            self.room.world,
            self.room.awareness.memory,
            self.inputs(),
            self.wish_context,
        )

    def inputs(self) -> SessionInputs:
        sleep = self.routine.sleep_context()
        if self._preparing_game is not None:
            sleep = replace(sleep, blocked=True)
        if (
            not self.state.sleeping
            and sleep.window(time.time())[0]
            and self.room.geometry.distance(
                self.room.position, self.room.geometry.anchor("bed")
            )
            > 40
        ):
            sleep = replace(sleep, blocked=True)
        return SessionInputs(
            time.time(),
            time.monotonic(),
            self.settings.auto_routine,
            None,
            False,
            False,
            None,
            sleep_context=sleep,
        )

    def _wake_from_clicks(self) -> None:
        outcome = self.router.dispatch(
            CareCommand("sleep", wake_from_clicks=True), inputs=self.inputs()
        )
        self.playback.speak(outcome.reaction)

    def _social_completed(self, completion: SocialCompletion) -> None:
        self.router.complete_social(
            completion,
            inputs=self.inputs(),
            arrangement_ready=not self.room.interaction.search_active,
        )

    def save(self) -> None:
        self.revision = self.store.save(
            self.state,
            self.settings,
            expected_revision=self.revision,
            adaptive=self.routine.memory,
            social_history=self.social_history,
            horoscope=self.horoscope_history,
            world=self.room.world.snapshot(),
            world_recovery_x=self.room.position.x,
            object_memory=self.room.awareness.memory.export(now=self.room.now),
        )
        self._last_saved = time.time()

    def tick(self) -> None:
        now = time.time()
        if self._suspended:
            return
        self.router.advance_time(self.inputs())
        elapsed = max(0, now - self._last_tick)
        self._last_tick = now
        self.playback.advance(min(elapsed, 1))
        self.room.update(min(elapsed, 0.5))
        if not self.playback.can_express():
            self.playback.express(None)
        if self.content is not None:
            self.content.update()
        if (
            self.settings.spontaneous_talk
            and not self.state.sleeping
            and self.games.sequence is None
            and self._preparing_game is None
            and not self.room.interaction.active
            and not self.playback.player.active
            and time.monotonic() >= self._next_comment
        ):
            wish = wish_to_express(
                self.state.wishes,
                elapsed=self.state.lived_seconds,
                sleeping=False,
                friendship_level=self.state.friendship_level,
                mood=self.state.mood,
                context=self.wish_context(),
                definitions=WISH_CATALOG.definitions,
            )
            reaction = (
                self.mind.wish_reaction(wish)
                if wish
                else self.mind.select_spontaneous_reaction(
                    self.state,
                    context_at(now),
                    time.monotonic(),
                )
            )
            self.playback.speak(reaction, require_presentation=False)
            self._next_comment = time.monotonic() + self.mind.rng.uniform(60, 140)
        if now - self._last_saved >= 5:
            self.save()

    def _cancel_game_preparation(self) -> None:
        if self._preparing_game is not None:
            self._preparing_game = None
            self.room.pause_route()
            self.game_snapshot = None

    def suspend(self) -> None:
        self.tick()
        self._cancel_game_preparation()
        if self.content is not None:
            self.content.suspend()
        self.games.close()
        self.game_snapshot = None
        self.room.suspend()
        self.playback.suspend()
        self._suspended = True
        self.save()

    def resume(self) -> None:
        if not self._suspended:
            return
        now = time.time()
        self.progression.advance(
            self.state,
            self.inputs(),
            max(0, now - self.state.updated_at),
            reconstruct=True,
        )
        self.clock.consume(wall_time=now)
        self._last_tick = now
        self._suspended = False
        self.save()

    def care(self, action: str) -> None:
        def perform() -> None:
            self.room.pause_route()
            self.playback.stop_animation()
            self.room.awareness.intentions.cancel(self.room.now)
            outcome = self.router.dispatch(
                CareCommand.from_action(action), inputs=self.inputs()
            )
            visual = care_animation(outcome.result, sleeping=self.state.sleeping)
            reaction = outcome.reaction
            if reaction is not None and visual is not None:
                reaction = replace(reaction, animation=visual)
            elif reaction is None:
                reaction = Reaction.spoken(
                    "care_fallback",
                    format_care_response(outcome.result),
                    visual or "idle",
                    "pet_refused" if outcome.result.affection_refused else action,
                )
            self.playback.speak(reaction)

        self.room.interaction.interrupt(perform)

    def execute(self, name: str, args: dict[str, Any]) -> None:
        if name not in ("resume", "suspend"):
            self.tick()
        if name == "care":
            self.care(str(args["action"]))
        elif name == "contact":
            self.contact.click("left")
        elif name == "call":
            self.room.call(RoomPoint(float(args["x"]), float(args.get("depth", 300))))
        elif name == "place":
            self.room.place(
                str(args["definition"]),
                RoomPoint(float(args["x"]), float(args.get("depth", 300))),
            )
        elif name == "move":
            self.room.relocate(
                str(args["instance"]),
                int(args["revision"]),
                RoomPoint(float(args["x"]), float(args.get("depth", 300))),
            )
        elif name == "offer":
            if "instance" in args:
                self.room.offer_existing(str(args["instance"]), int(args["revision"]))
            else:
                self.room.offer(str(args["definition"]))
        elif name == "object_drag_start":
            self.room.begin_drag(
                str(args["instance"]) if "instance" in args else None,
                int(args.get("revision", 0)),
                definition=str(args["definition"]) if "definition" in args else None,
            )
        elif name == "object_drag_move":
            self.room.move_drag(
                RoomPoint(float(args["x"]), float(args["depth"])),
                float(args["height"]),
                inside=args.get("inside") is True,
                face=(float(args["face_x"]), float(args["face_y"]))
                if "face_x" in args and "face_y" in args
                else None,
            )
        elif name == "object_drag_drop":
            self.room.drop_drag(
                RoomPoint(float(args["x"]), float(args["depth"])),
                offer=args.get("offer") is True,
                height=float(args.get("height", 0)),
            )
        elif name == "object_drag_cancel":
            self.room.cancel_drag()
        elif name == "speech_next":
            self.playback.next_text()
        elif name == "speech_ack":
            self.playback.acknowledge(int(args["id"]))
        elif name == "game_open":
            result = self.router.dispatch(CareCommand("play"), inputs=self.inputs())
            if result.result.effect == CareEffect.PLAY_TIRED:
                self.playback.speak(result.reaction)
            else:

                def open_game() -> None:
                    self._cancel_game_preparation()
                    self.playback.player.cancel()
                    game_id = str(args["id"])
                    if game_id == "connect_four":
                        self.games.close()
                        self._preparing_game = game_id
                        self.game_snapshot = {"id": game_id, "preparing": True}

                        def arrived(success: bool) -> None:
                            self._preparing_game = None
                            self.game_snapshot = None
                            if success:
                                self.games.open(game_id)
                                self.game_snapshot = self.games.snapshot()

                        try:
                            self.room.prepare_activity(
                                self.room.geometry.anchor("table"), arrived
                            )
                        except ValueError:
                            self._preparing_game = None
                            self.game_snapshot = None
                            raise
                    else:
                        self.games.open(game_id)
                        self.game_snapshot = self.games.snapshot()

                self.room.interaction.interrupt(open_game)
        elif name == "game_action":
            self.games.action(str(args["action"]), args.get("value"))
        elif name == "game_close":
            self._cancel_game_preparation()
            self.games.close()
            self.game_snapshot = None
        elif name == "wish_pin":
            self.router.set_wish_pinned(
                int(args["id"]), bool(args["pinned"]), inputs=self.inputs()
            )
        elif name in ("social", "horoscope"):
            if self.content is not None:
                self.content.select(
                    "horoscope" if name == "horoscope" else str(args["category"])
                )
        elif name == "wish_dismiss":
            self.router.dismiss_wish(int(args["id"]), inputs=self.inputs())
        elif name == "settings":
            raw = dict(self.settings.to_dict())
            allowed = {
                "zodiac_sign",
                "online_social",
                "auto_routine",
                "spontaneous_talk",
                "auto_walk",
                "scale",
                "ui_scale_percent",
            }
            if set(args) - allowed:
                raise ValueError("Unbekannte Zimmereinstellung.")
            raw.update(args)
            self.settings = PetSettings.from_dict(raw)
            if self.content is not None:
                self.content.runtime.set_enabled(self.settings.online_social)
        elif name == "suspend":
            self.suspend()
        elif name == "resume":
            self.resume()
        elif name not in ("tick", "snapshot", "forecast"):
            raise ValueError("Diese Zimmeraktion ist nicht verfügbar.")
        if name not in (
            "tick",
            "snapshot",
            "speech_ack",
            "suspend",
            "resume",
            "forecast",
            "object_drag_move",
        ):
            self.save()

    def snapshot(self) -> dict[str, Any]:
        world = self.room.world.snapshot()
        self.game_snapshot = (
            {"id": self._preparing_game, "preparing": True}
            if self._preparing_game
            else self.games.snapshot()
        )
        status = project_status(
            snapshot_pet(self.state, wish_context=self.wish_context()),
            context_at(time.time()),
            None,
            ComputerSnapshot(),
            observe_computer=False,
        )
        return {
            "revision": self.revision.value,
            "pet": json_value(self.state.capture_checkpoint()),
            "room": json_value(world.room),
            "objects": json_value(world.objects),
            "speech": json_value(self.playback.snapshot()),
            "drag": {
                "instance_id": self.room.drag_instance,
                "ready": self.room.drag_ready,
            },
            "animation": (
                "sleep"
                if self.state.sleeping
                else "pick_up"
                if self.room.drag_ready and self.playback.animation == "idle"
                else EXPRESSION_CLIPS[self.playback.expression]
                if self.playback.expression is not None and not self.room.moving
                else self.room.locomotion.selection.animation
                if self.playback.animation == "idle"
                else self.playback.animation
            ),
            "moving": self.room.moving,
            "facing": self.room.facing,
            "heading": self.room.movement.heading(
                self.room.position, self.room.environment.heading,
            ),
            "motion": {
                "serial": self.room.movement.serial,
                "time": self.room.now,
                "travelled": json_value(self.room.movement.travelled)
                if self.room.moving
                else [],
            },
            "held_item": (
                self.games.effects.held_item
                if self.games.effects and self.games.effects.held_item
                else self.room.held_item
            ),
            "game": self.game_snapshot,
            "held_pose": self.room.held_pose,
            "animation_id": self.playback.action_id,
            "animation_timings": self.playback.action_timings,
            "animation_hold_frame": (
                7
                if self.room.drag_ready and self.playback.animation == "idle"
                else self.room.locomotion.selection.fixed_frame
                if self.playback.animation == "idle"
                and self.playback.expression is None
                and not self.state.sleeping
                else self.playback.hold_frame
            ),
            "social": json_value(self.content.runtime.snapshot())
            if self.content
            else None,
            "horoscope": self.content.horoscope.availability()
            if self.content
            else None,
            "catalog": {
                "moodlet_icons": MOODLET_ICONS,
                "moodlet_descriptions": {
                    str(view.value.instance_id): moodlet_description(view)
                    for view in status.emotional.moodlets
                },
                "wish_descriptions": {
                    str(view.value.instance_id): wish_description(view)
                    for view in status.emotional.wishes
                },
                "foods": [
                    json_value(DEFAULT_CATALOG.foods[key])
                    for key in DEFAULT_CATALOG.menu_order
                    if key in DEFAULT_CATALOG.foods
                ],
                "wishes": [
                    json_value(item) for item in WISH_CATALOG.definitions.values()
                ],
                "moodlets": [
                    json_value(item) for item in MOODLET_CATALOG.definitions.values()
                ],
                "settings": self.settings.to_dict(),
                "status": json_value(status),
            },
            "error": self.error,
        }
