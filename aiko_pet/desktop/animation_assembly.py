"""Compose desktop animation, observation, movement and Tk sprite owners.

Construction belongs to the desktop composition boundary, while each object
retains its own behavior. There is one walk controller and one ambient policy.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from ..application.settings import PetSettings
from ..pet.animation.character import CharacterCatalog
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.movement.contracts import HorizontalTrack
from ..pet.state import PetState
from ..infrastructure.hardware.monitor import ActivityMonitor
from ..infrastructure.item_assets import load_item_catalog
from ..ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from .animation_runtime import AnimationRuntimePorts, DesktopAnimationRuntime
from .visual_observation import DesktopVisualObservation
from .walk_runtime import WalkDriver, WalkDriverPorts


@dataclass(frozen=True, slots=True)
class AnimationAssemblyPorts:
    """Host callbacks needed to connect the owners, not a GUI shell."""

    track: Callable[[], HorizontalTrack]
    toolbar_visible: Callable[[], bool]
    place_x: Callable[[float], None]
    walk_finished: Callable[[float], None]
    gaze_origin: Callable[[], tuple[float, float]]
    game_mode: Callable[[], bool]
    action_until: Callable[[], float]
    action_state: Callable[[], str]
    attention_until: Callable[[], float]
    extend_action: Callable[[float], None]


@dataclass(frozen=True, slots=True)
class AnimationComponents:
    """The four distinct owners of one desktop pet's visual motion."""

    walk: WalkDriver
    visual: DesktopVisualObservation
    animation: DesktopAnimationRuntime
    sprite: AnimatedPet


def assemble_animation(
    *, root: tk.Tk, canvas: tk.Canvas, state: PetState,
    settings: PetSettings, adaptive: AdaptiveRoutine,
    monitor: ActivityMonitor, assets: CharacterCatalog,
    ports: AnimationAssemblyPorts,
) -> AnimationComponents:
    """Wire a single runtime graph without claiming its mutable state."""
    walk = WalkDriver(
        state=state, settings=settings, adaptive=adaptive, monitor=monitor,
        walk_cycle_seconds=assets.clips["running-left"].duration_seconds,
        ports=WalkDriverPorts(
            track=ports.track,
            toolbar_visible=ports.toolbar_visible,
            place_x=ports.place_x,
            walk_finished=ports.walk_finished,
        ),
    )
    visual = DesktopVisualObservation(
        settings=settings, monitor=monitor, eyes=ports.gaze_origin,
    )
    animation = DesktopAnimationRuntime(
        state=state, settings=settings, assets=assets, walk=walk, visual=visual,
        ports=AnimationRuntimePorts(
            action_until=ports.action_until,
            action_state=ports.action_state,
            attention_until=ports.attention_until,
        ),
    )
    sprite = AnimatedPet(
        root, canvas, state, settings,
        AnimatedPorts(
            walk_step=lambda now, elapsed: animation.advance_walk(
                now, elapsed, game_mode=ports.game_mode(),
            ),
            walk_active=animation.walk_active,
            interrupt_walk=animation.interrupt_walk,
            choose_animation=animation.choose,
            reset_gaze=visual.reset,
            extend_action=ports.extend_action,
        ),
        assets=assets, items=load_item_catalog(),
        ambient=animation.ambient,
    )
    return AnimationComponents(walk, visual, animation, sprite)
