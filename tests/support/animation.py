"""Animation fixtures independent of unittest case lifecycles."""

from __future__ import annotations

import random
import tkinter as tk
from contextlib import ExitStack, contextmanager
from typing import cast
from unittest.mock import MagicMock, Mock

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.attention import AttentionCoordinator
from aiko_pet.application.controller import CareController
from aiko_pet.application.router import ApplicationRouter
from aiko_pet.application.settings import PetSettings
from aiko_pet.desktop.animation_runtime import (
    AnimationRuntimePorts,
    DesktopAnimationRuntime,
)
from aiko_pet.desktop.attention_runtime import (
    AttentionRuntimePorts,
    DesktopAttentionRuntime,
)
from aiko_pet.desktop.geometry import TaskbarTrack
from aiko_pet.desktop.visual_observation import (
    DesktopVisualObservation,
    VisualAttentionPorts,
)
from aiko_pet.desktop.walk_runtime import WalkDriver, WalkDriverPorts
from aiko_pet.infrastructure.character_assets import load_character_catalog
from aiko_pet.infrastructure.character_mind import make_aiko_mind
from aiko_pet.infrastructure.item_assets import load_item_catalog
from aiko_pet.pet.animation.animation import PassiveObservation
from aiko_pet.pet.animation.character import FRAME_WIDTH
from aiko_pet.pet.animation.idle_gesture import with_idle_gestures
from aiko_pet.pet.animation.priority import RenderDecision
from aiko_pet.pet.emotions import EmotionalComposition, EmotionalState
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.mind.cursor_behaviour import CursorIntent
from aiko_pet.pet.mind.workload_events import WorkloadEventDetector
from aiko_pet.pet.routine import context_at
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot
from aiko_pet.ui.pet_view.animated_pet import AnimatedPet, AnimatedPorts
from aiko_pet.ui.pet_view.attention_presenter import AttentionPresenter


class IdleMonitor:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot(cpu=2)


class AnimatedPetFixture:
    def prepare_fixture(self, cleanup) -> None:
        self.root = tk.Tk()
        cleanup(self.root.destroy)
        self.root.withdraw()
        self.canvas = tk.Canvas(self.root, width=192, height=208)
        self.canvas.pack()
        self.state = PetState()
        self.settings = PetSettings(x=100, y=500)
        self.action_deadlines: list[float] = []
        assets = with_idle_gestures(load_character_catalog())
        self.walk = WalkDriver(
            state=self.state,
            settings=self.settings,
            adaptive=AdaptiveRoutine(),
            monitor=IdleMonitor(),
            walk_cycle_seconds=assets.clips["running-left"].duration_seconds,
            ports=WalkDriverPorts(
                track=lambda: TaskbarTrack(0, 800, 800), place_x=self._place_x
            ),
        )
        self.selected_cursor = CursorIntent()
        self.visual = DesktopVisualObservation(
            settings=self.settings,
            monitor=IdleMonitor(),
            attention=VisualAttentionPorts(cursor_intent=lambda: self.selected_cursor),
            eyes=lambda: (
                self.root.winfo_x() + FRAME_WIDTH // 2 * self.settings.scale,
                self.root.winfo_y() + 82 * self.settings.scale,
            ),
        )
        self.animation = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=assets,
            walk=self.walk,
            visual=self.visual,
            ports=AnimationRuntimePorts(
                action_until=lambda: 0.0, action_clip_id=lambda: "idle"
            ),
        )
        self.anim = AnimatedPet(
            self.root,
            self.canvas,
            self.state,
            self.settings,
            AnimatedPorts(
                walk_step=self._step_walk,
                walk_active=self.animation.walk_active,
                interrupt_walk=self.animation.interrupt_walk,
                choose_animation=self.animation.select_animation,
                reset_gaze=self.visual.reset,
                extend_action=self.action_deadlines.append,
            ),
            assets=assets,
            items=load_item_catalog(),
            ambient=self.animation.ambient,
        )
        cleanup(self.anim.close)

    def _place_x(self, value: float) -> None:
        self.settings.x = round(value)

    def _gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        self.selected_cursor = CursorIntent("observe", target=pointer)
        return self.visual.gaze_direction(pointer, game_mode=self.anim.game_mode)

    def _step_walk(self, now: float, elapsed: float) -> str | None:
        return self.animation.advance_walk(now, elapsed, game_mode=self.anim.game_mode)


class StaticReadings:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()


class AttentionFixture:
    def prepare_fixture(self) -> None:
        self.state = PetState()
        self.settings = PetSettings()
        self.mind = make_aiko_mind(started_at=0.0, rng=random.Random(7))
        self.workload_events = WorkloadEventDetector(rng=random.Random(8))
        self.router = ApplicationRouter(
            CareController(
                self.state,
                self.mind,
                AdaptiveRoutine(),
                clock=ActiveSessionClock(lambda: 0.0),
            )
        )
        self.attention = AttentionCoordinator(
            self.state,
            self.settings,
            self.mind,
            self.workload_events,
            StaticReadings(),
            self.router,
            started_at=100.0,
        )


class AnimationRuntimeFixture:
    def create_runtime_fixture(self) -> None:
        self.state = PetState()
        self.settings = PetSettings()
        self.walk = MagicMock(spec=WalkDriver)
        self.walk.movement = MagicMock()
        self.walk.movement.remaining_distance = 0
        self.walk.step.return_value = None
        self.visual = MagicMock(spec=DesktopVisualObservation)
        self.visual.observe.return_value = PassiveObservation(None, False)
        self.visual.orienting = False
        self.visual.cursor_watching = False
        self.visual.cursor_intent = CursorIntent()
        self.action_until = 0.0
        self.action_clip_id = "review"
        self.holding_readable = False
        self.ready_for_handover = False
        self.assets = load_character_catalog()
        self.runtime = DesktopAnimationRuntime(
            state=self.state,
            settings=self.settings,
            assets=self.assets,
            walk=cast(WalkDriver, self.walk),
            visual=cast(DesktopVisualObservation, self.visual),
            ports=AnimationRuntimePorts(
                action_until=lambda: self.action_until,
                action_clip_id=lambda: self.action_clip_id,
                holding_readable=lambda: self.holding_readable,
                ready_for_handover=lambda: self.ready_for_handover,
            ),
        )
        self.runtime.ambient.next_blink_at = 1000.0
        self.runtime.ambient.next_glance_at = 1000.0

    def choose(
        self,
        *,
        now: float = 100.0,
        game_mode: bool = False,
        active_action: str | None = None,
    ) -> RenderDecision:
        return self.runtime.select_animation(
            now, (100, 0), now - 1, game_mode, active_action
        )


class AttentionRuntimeFixture:
    def prepare_fixture(self) -> None:
        self.attention = Mock(spec=AttentionCoordinator)
        self.attention.state = PetState()
        self.attention.mind = Mock()
        self.attention.mind.emotional_state.return_value = EmotionalComposition(
            EmotionalState.SATISFIED
        )
        self.presenter = Mock(spec=AttentionPresenter)
        self.context = context_at(1781000000.0)
        self.toolbar_refresh = Mock()
        self.runtime = DesktopAttentionRuntime(
            self.attention,
            self.presenter,
            AttentionRuntimePorts(
                context=lambda: self.context,
                game_open=lambda: False,
                bubble_visible=lambda: False,
                reaction_pending=lambda: False,
                walking=lambda: False,
                action_until=lambda: 0.0,
                refresh_toolbar=self.toolbar_refresh,
            ),
        )


@contextmanager
def animated_fixture():
    with ExitStack() as resources:
        fixture = AnimatedPetFixture()
        fixture.prepare_fixture(resources.callback)
        yield fixture
