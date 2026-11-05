"""One portable Tamagotchi session composed from the existing rule owners."""

from __future__ import annotations

import time
from typing import Any

from ..pet.animation.character import CharacterCatalog
from ..pet.care_result import CareEffect
from ..pet.food_catalog import DEFAULT_CATALOG
from ..pet.interaction_events import SocialCompletion
from ..pet.mind import PetMind
from ..pet.moodlet_catalog import MOODLET_CATALOG
from ..pet.wish_catalog import WISH_CATALOG
from ..presentation.room_playback import RoomPlayback
from ..world.contracts import WorldSurface
from ..world.room import RoomPoint
from ..world.state import WorldState
from .active_time import ActiveSessionClock, SessionInputs
from .commands import CareCommand
from .controller import CareController
from .game_experience import GameExperienceCoordinator
from .game_sessions import GameSessionCoordinator
from .room import RoomCoordinator
from .room_contracts import json_value
from .room_routine import RoomRoutine
from .router import ApplicationRouter
from .session import LoadedPetData, SavedPetStore
from .settings import PetSettings


class RoomSession:
    """No duplicate pet values, clock, inventory, dialogue or reward rules."""

    def __init__(
        self, store: SavedPetStore, loaded: LoadedPetData, mind: PetMind,
        world: WorldState, animations: CharacterCatalog,
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
        self.game_snapshot: dict[str, Any] | None = None
        self._suspended = False
        self._last_tick = time.time()
        self._last_saved = self._last_tick
        self.playback = RoomPlayback(
            animations, social_completed=self._social_completed,
            mark_spoken=lambda: self.mind.record_care_contact(time.monotonic()),
        )
        if loaded.world is not None:
            world.restore_snapshot(loaded.world)
        world.change_surface(WorldSurface(5100, 900, 24), recovering=True)
        self.room = RoomCoordinator(
            world, self.state, mind, self.routine, self.clock, self.playback,
            memory=loaded.object_memory, inputs=self.inputs,
            game_open=lambda: self.game_snapshot is not None,
        )
        self.router = ApplicationRouter(
            CareController(self.state, mind, self.routine, clock=self.clock,
                           progression=self.room.progression),
            game_experience=GameExperienceCoordinator(
                self.state, mind, self.routine, clock=self.clock,
                progression=self.room.progression,
                arrangement_ready=lambda: not self.room.interaction.search_active,
            ),
        )
        self.games = GameSessionCoordinator(self.router, self.state, mind,
                                            self.playback, self.inputs)
        if loaded.restored_from_save:
            self.room.progression.advance(
                self.state, self.inputs(), max(0, time.time() - self.state.updated_at),
                reconstruct=True,
            )
        self.state.anchor_live_session(time.time())
        self.clock.consume(wall_time=time.time())

    def inputs(self) -> SessionInputs:
        return SessionInputs(
            time.time(), time.monotonic(), self.settings.auto_routine,
            None, False, False, None, sleep_context=self.routine.sleep_context(),
        )

    def _social_completed(self, completion: SocialCompletion) -> None:
        self.router.complete_social(
            completion, inputs=self.inputs(),
            arrangement_ready=not self.room.interaction.search_active,
        )

    def save(self) -> None:
        self.revision = self.store.save(
            self.state, self.settings, expected_revision=self.revision,
            adaptive=self.routine.memory, social_history=self.social_history,
            horoscope=self.horoscope_history,
            world=self.room.world.snapshot(), world_recovery_x=self.room.position.x,
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
        if now - self._last_saved >= 5:
            self.save()

    def suspend(self) -> None:
        self.tick()
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
        self.room.progression.advance(
            self.state, self.inputs(), max(0, now - self.state.updated_at),
            reconstruct=True,
        )
        self.clock.consume(wall_time=now)
        self._last_tick = now
        self._suspended = False
        self.save()

    def care(self, action: str) -> None:
        def perform() -> None:
            outcome = self.router.dispatch(CareCommand.from_action(action), inputs=self.inputs())
            self.playback.speak(outcome.reaction)
        self.room.interaction.interrupt(perform)

    def execute(self, name: str, args: dict[str, Any]) -> None:
        if name not in ("resume", "suspend"):
            self.tick()
        if name == "care":
            self.care(str(args["action"]))
        elif name == "call":
            self.room.call(RoomPoint(float(args["x"]) % 5100, float(args.get("depth", 1.1))))
        elif name == "place":
            self.room.place(str(args["definition"]), RoomPoint(float(args["x"]) % 5100,
                                                               float(args.get("depth", .9))))
        elif name == "move":
            self.room.relocate(str(args["instance"]), int(args["revision"]),
                               RoomPoint(float(args["x"]) % 5100, float(args.get("depth", .9))))
        elif name == "offer":
            self.room.offer(str(args["definition"]))
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
                    self.playback.player.cancel()
                    self.games.open(str(args["id"]))
                    self.game_snapshot = self.games.snapshot()
                self.room.interaction.interrupt(open_game)
        elif name == "game_action":
            self.games.action(str(args["action"]), args.get("value"))
        elif name == "game_close":
            self.games.close()
            self.game_snapshot = None
        elif name == "wish_pin":
            self.router.set_wish_pinned(int(args["id"]), bool(args["pinned"]), inputs=self.inputs())
        elif name == "wish_dismiss":
            self.router.dismiss_wish(int(args["id"]), inputs=self.inputs())
        elif name == "settings":
            raw = dict(self.settings.to_dict())
            allowed = {"zodiac_sign", "online_social", "auto_routine", "spontaneous_talk"}
            if set(args) - allowed:
                raise ValueError("Unbekannte Zimmereinstellung.")
            raw.update(args)
            self.settings = PetSettings.from_dict(raw)
        elif name == "suspend":
            self.suspend()
        elif name == "resume":
            self.resume()
        elif name not in ("tick", "snapshot"):
            raise ValueError("Diese Zimmeraktion ist nicht verfügbar.")
        if name not in ("tick", "snapshot", "speech_ack", "suspend", "resume"):
            self.save()

    def snapshot(self) -> dict[str, Any]:
        world = self.room.world.snapshot()
        self.game_snapshot = self.games.snapshot()
        return {
            "revision": self.revision.value,
            "pet": json_value(self.state.capture_checkpoint()),
            "room": json_value(world.room), "objects": json_value(world.objects),
            "speech": json_value(self.playback.snapshot()),
            "animation": self.playback.animation,
            "moving": self.room.moving, "facing": self.room.facing,
            "held_item": self.room.held_item, "game": self.game_snapshot,
            "catalog": {
                "foods": [json_value(DEFAULT_CATALOG.foods[key]) for key in DEFAULT_CATALOG.menu_order
                          if key in DEFAULT_CATALOG.foods],
                "wishes": [json_value(item) for item in WISH_CATALOG.definitions.values()],
                "moodlets": [json_value(item) for item in MOODLET_CATALOG.definitions.values()],
                "settings": self.settings.to_dict(),
            },
            "error": self.error,
        }
