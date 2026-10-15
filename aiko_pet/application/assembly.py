"""Compose application services without any desktop or UI dependency."""

from __future__ import annotations

from dataclasses import dataclass

from ..pet.mind import PetMind
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.workload_events import WorkloadEventDetector
from ..pet.state import PetState
from .active_time import ActiveSessionClock
from .activity import ActivityCallbacks, ActivityCoordinator
from .controller import CareController
from .cursor_observation import CursorObservation
from .game_experience import GameExperienceCoordinator
from .ports import ComputerObservation
from .router import ApplicationRouter
from .settings import PetSettings


@dataclass(frozen=True, slots=True)
class ApplicationComponents:
    """Single-instance use-case owners with a shared running-session clock."""

    router: ApplicationRouter
    activity: ActivityCoordinator
    workload_events: WorkloadEventDetector
    cursor_observation: CursorObservation


def assemble_application(
    *, state: PetState, settings: PetSettings, mind: PetMind,
    adaptive: AdaptiveRoutine, monitor: ComputerObservation,
    callbacks: ActivityCallbacks, clock: ActiveSessionClock,
) -> ApplicationComponents:
    """Build one coherent graph; no duplicate pet or conversation memory."""
    cursor_observation = CursorObservation(mind.cursor_attention)
    router = ApplicationRouter(
        CareController(state, mind, adaptive, clock=clock),
        game_experience=GameExperienceCoordinator(
            state, mind, adaptive, clock=clock,
        ),
    )
    workload_events = WorkloadEventDetector()
    activity = ActivityCoordinator(
        state, settings, mind, adaptive, workload_events, monitor,
        callbacks, clock=clock,
    )
    return ApplicationComponents(router, activity, workload_events, cursor_observation)
