"""Compatibility entrypoints for pre-refactor desktop view consumers.

German presentation is computed exactly once by the canonical projection
functions. Old PetState-based signatures and DesktopViewSource attributes
remain available, without duplicating layout or localized text.
"""

from __future__ import annotations

from typing import Callable

from ..application.ports import ComputerReadings
from ..application.read_snapshot import snapshot_pet
from ..application.settings import PetSettings
from ..personality.adaptive import AdaptiveRoutine
from ..personality.adaptive_models import Behaviour
from ..personality.mind import AikoMind
from ..pet.routine import TimeContext
from ..pet.state import PetState
from ..telemetry import ComputerSnapshot
from .contracts import HoverSnapshot, StatusSnapshot
from .projections import (
    project_hover as project_hover_snapshot,
    project_settings as project_settings,
    project_status as project_status_snapshot,
)
from .read_models import DesktopPresentation


def project_hover(
    state: PetState,
    context: TimeContext,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
) -> HoverSnapshot:
    """Support the former PetState signature through a semantic snapshot."""
    return project_hover_snapshot(
        snapshot_pet(state), context, computer,
        observe_computer=observe_computer,
    )


def project_status(
    state: PetState,
    context: TimeContext,
    mind: AikoMind,
    situation: Behaviour | None,
    computer: ComputerSnapshot,
    *,
    observe_computer: bool,
    now: float,
) -> StatusSnapshot:
    """Support the former status arguments without duplicating UI copy."""
    return project_status_snapshot(
        snapshot_pet(state), context, mind.emotion(state, now),
        situation, computer, observe_computer=observe_computer,
    )


class DesktopViewSource(DesktopPresentation):
    """Historical view adapter with the original public component handles."""

    def __init__(
        self, state: PetState, settings: PetSettings, mind: AikoMind,
        adaptive: AdaptiveRoutine, monitor: ComputerReadings,
        *, context: Callable[[], TimeContext],
        sprite_size: Callable[[], tuple[int, int]],
    ) -> None:
        super().__init__(
            state, settings, mind, adaptive, monitor,
            context=context, sprite_size=sprite_size,
        )
        # Existing integrations may read these references directly.
        self.state = state
        self.settings = settings
        self.mind = mind
        self.adaptive = adaptive
        self.monitor = monitor
