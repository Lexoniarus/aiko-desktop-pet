"""Capabilities needed by room conversations, independent of their host."""

from typing import Protocol

from ..application.active_time import SessionInputs
from ..application.horoscope_models import HoroscopeHistory
from ..application.router import ApplicationRouter
from ..application.settings import PetSettings
from ..application.social_history import SocialContentHistory
from ..pet.mind import PetMind
from ..pet.state import PetState
from .games.session import GameSessionCoordinator
from .room_playback import RoomPlayback
from .room_runtime import RoomRuntime


class RoomContentHost(Protocol):
    state: PetState
    settings: PetSettings
    mind: PetMind
    social_history: SocialContentHistory
    horoscope_history: HoroscopeHistory
    router: ApplicationRouter
    games: GameSessionCoordinator
    playback: RoomPlayback
    room: RoomRuntime

    def inputs(self) -> SessionInputs: ...

    def save(self) -> None: ...
