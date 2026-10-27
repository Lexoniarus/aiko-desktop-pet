"""Compose desktop animation, observation, movement and Tk sprite owners.

Construction belongs to the desktop composition boundary, while each object
retains its own behavior. There is one walk controller and one ambient policy.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from ..application.contact import ContactCoordinator
from ..application.cursor_behaviour import CursorBehaviourCoordinator
from ..application.cursor_observation import CursorObservation
from ..application.settings import PetSettings
from ..infrastructure.hardware.monitor import ActivityMonitor
from ..infrastructure.item_assets import load_item_catalog
from ..pet.animation.character import CharacterCatalog
from ..pet.animation.item_assets import ItemCatalog
from ..pet.mind.adaptive import AdaptiveRoutine
from ..pet.mind.cursor_behaviour import CursorIntent
from ..pet.movement.contracts import HorizontalTrack
from ..pet.state import PetState
from ..ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from ..ui.windows.hover_ui import HoverUi
from .animation_runtime import AnimationRuntimePorts, DesktopAnimationRuntime
from .attention_runtime import DesktopAttentionRuntime
from .input import DesktopInput
from .pointer_runtime import PointerRuntime, PointerRuntimePorts
from .visual_observation import DesktopVisualObservation, VisualAttentionPorts
from .walk_runtime import WalkDriver, WalkDriverPorts
from .world_access import WorldRuntimeAccess


def assemble_pointer(
    observer: CursorObservation,
    behaviour: CursorBehaviourCoordinator,
    inputs: DesktopInput,
    animated: AnimatedPet,
    settings: PetSettings,
    attention: DesktopAttentionRuntime,
    contact: ContactCoordinator,
    hover: HoverUi,
    world: WorldRuntimeAccess,
    walk: WalkDriver,
) -> PointerRuntime:
    """Keep pointer wiring at the existing desktop composition boundary."""
    return PointerRuntime(
        observer,
        PointerRuntimePorts(
            sample=inputs.pointer_sample,
            game_mode=lambda: animated.game_mode,
            eyes=lambda: animated.cursor_eye_position,
            on_motion=attention.cursor_moved,
            scale=lambda: settings.scale,
            menu_engaged=lambda: hover.menu_engaged,
            foreground_active=lambda: not contact.can_interact("pet"),
            world_protected=world.cursor_protected,
            pointer_inside=hover.pointer_inside,
        ),
        behaviour=behaviour,
        walk=walk,
    )


@dataclass(frozen=True, slots=True)
class AnimationAssemblyPorts:
    """Host callbacks needed to connect the owners, not a GUI shell."""

    track: Callable[[], HorizontalTrack]
    menu_engaged: Callable[[], bool]
    place_x: Callable[[float], None]
    walk_finished: Callable[[float], None]
    gaze_origin: Callable[[], tuple[float, float]]
    game_mode: Callable[[], bool]
    action_until: Callable[[], float]
    action_clip_id: Callable[[], str]
    attention_until: Callable[[], float]
    extend_action: Callable[[float], None]
    world: WorldRuntimeAccess
    feedback_subject: Callable[[], str | None] = lambda: None
    activity_active: Callable[[], bool] = lambda: False
    cursor_intent: Callable[[], CursorIntent] = CursorIntent
    cursor_allowed: Callable[[], bool] = lambda: False
    cursor_finished: Callable[[int, float], None] = lambda _token, _now: None


@dataclass(frozen=True, slots=True)
class AnimationComponents:
    """The four distinct owners of one desktop pet's visual motion."""

    walk: WalkDriver
    visual: DesktopVisualObservation
    animation: DesktopAnimationRuntime
    sprite: AnimatedPet
    items: ItemCatalog


def assemble_animation(
    *,
    root: tk.Tk,
    canvas: tk.Canvas,
    state: PetState,
    settings: PetSettings,
    adaptive: AdaptiveRoutine,
    monitor: ActivityMonitor,
    assets: CharacterCatalog,
    ports: AnimationAssemblyPorts,
) -> AnimationComponents:
    """Wire a single runtime graph without claiming its mutable state."""
    walk = WalkDriver(
        state=state,
        settings=settings,
        adaptive=adaptive,
        monitor=monitor,
        walk_cycle_seconds=assets.clips["running-left"].duration_seconds,
        ports=WalkDriverPorts(
            track=ports.track,
            menu_engaged=ports.menu_engaged,
            place_x=ports.place_x,
            walk_finished=ports.walk_finished,
            committed_goal=ports.world.focused,
            cursor_allowed=ports.cursor_allowed,
            cursor_finished=ports.cursor_finished,
            idle_steps=lambda: "body-step-right-profil" in assets.body_clips,
        ),
    )
    visual = DesktopVisualObservation(
        settings=settings,
        monitor=monitor,
        eyes=ports.gaze_origin,
        attention=VisualAttentionPorts(
            phase=ports.world.phase,
            sleeping=lambda: state.sleeping,
            walking=lambda: walk.movement.remaining_distance,
            following_subject=ports.world.following_record,
            feedback_subject=ports.feedback_subject,
            activity_active=ports.activity_active,
            orientation_side=ports.world.orientation_side,
            cursor_intent=ports.cursor_intent,
            walk_kind=lambda: walk.movement.kind,
        ),
    )
    animation = DesktopAnimationRuntime(
        state=state,
        settings=settings,
        assets=assets,
        walk=walk,
        visual=visual,
        ports=AnimationRuntimePorts(
            action_until=ports.action_until,
            action_clip_id=ports.action_clip_id,
            attention_until=ports.attention_until,
            ready_for_handover=ports.world.ready_for_handover,
            holding_readable=ports.world.holding_readable,
            cursor_gaze_point=ports.world.cursor_gaze_point,
        ),
    )
    items = load_item_catalog()
    sprite = AnimatedPet(
        root,
        canvas,
        state,
        settings,
        AnimatedPorts(
            walk_step=lambda now, elapsed: animation.advance_walk(
                now,
                elapsed,
                game_mode=ports.game_mode(),
            ),
            walk_active=animation.walk_active,
            interrupt_walk=animation.interrupt_walk,
            choose_animation=animation.select_animation,
            reset_gaze=visual.reset,
            extend_action=ports.extend_action,
        ),
        assets=assets, items=items,
        ambient=animation.ambient,
    )
    return AnimationComponents(walk, visual, animation, sprite, items)
