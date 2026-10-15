"""Own desktop startup and resource shutdown without domain decisions.

Unlike the Tk composition root, this lifecycle owns only the lifetime and
ordering of already constructed services. It never creates alternate state.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ..application.router import ApplicationRouter
from ..infrastructure.hardware.monitor import ActivityMonitor
from ..ui.pet_view.reaction_player import ReactionPlayer
from ..ui.pet_view.speech_presenter import SpeechPresenter
from ..ui.windows.hover_ui import HoverUi
from .input import DesktopInput
from .runtime import DesktopRuntime
from .window_stack import WindowStack


class DesktopLifecycle:
    """Start/stop desktop services once with the existing teardown order."""

    def __init__(
        self, *, root: tk.Tk, inputs: DesktopInput,
        runtime: DesktopRuntime, monitor: ActivityMonitor,
        application: ApplicationRouter, overlays: WindowStack,
        hover: HoverUi, reaction: ReactionPlayer,
        speech: SpeechPresenter, place_initially: Callable[[], None],
        save: Callable[[], None], stop_animation: Callable[[], None],
    ) -> None:
        self._root = root
        self._inputs = inputs
        self._runtime = runtime
        self._monitor = monitor
        self._application = application
        self._overlays = overlays
        self._hover = hover
        self._reaction = reaction
        self._speech = speech
        self._place_initially = place_initially
        self._save = save
        self._stop_animation = stop_animation
        self._started = False
        self._stopped = False

    def start(self) -> None:
        """Map the sprite only after its actual taskbar geometry is applied."""
        if self._started or self._stopped:
            return
        self._started = True
        self._inputs.initialize()
        self._place_initially()
        self._root.update_idletasks()
        self._root.deiconify()
        self._overlays.restore()
        self._monitor.start()
        self._runtime.start()

    def prepare_farewell(self) -> None:
        """Quiesce input and ambient effects while keeping the sprite alive."""
        if self._stopped:
            return
        self._runtime.stop()
        self._inputs.stop()
        self._reaction.cancel()
        self._hover.close_game()
        self._hover.close_settings()
        self._hover.close_toolbar()

    def stop(self) -> None:
        """Close background services before destroying any Tk-owned widget."""
        if self._stopped:
            return
        self._stopped = True
        self._runtime.stop()
        self._inputs.stop()
        # Finish any game while its reward router remains open, before saving.
        self._hover.close_game()
        self._application.close()
        self._stop_animation()
        self._monitor.stop()
        self._save()
        self._reaction.cancel()
        self._speech.hide()
        self._hover.close_settings()
        self._hover.close_toolbar()
        self._root.destroy()
