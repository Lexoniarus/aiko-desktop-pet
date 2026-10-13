"""Own desktop startup and resource shutdown without domain decisions.

Unlike the Tk composition root, this lifecycle owns only the lifetime and
ordering of already constructed services. It never creates alternate state.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable

from ..application.router import ApplicationRouter
from ..presentation.reaction_playback import ReactionPlayer
from ..infrastructure.hardware.monitor import ActivityMonitor
from ..ui.hover_ui import HoverUi
from ..ui.speech_presenter import SpeechPresenter
from .window_stack import WindowStack
from .input import DesktopInput
from .runtime import DesktopRuntime


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

    def stop(self) -> None:
        """Close background services before destroying any Tk-owned widget."""
        if self._stopped:
            return
        self._stopped = True
        self._application.close()
        self._runtime.stop()
        self._stop_animation()
        self._inputs.stop()
        self._monitor.stop()
        self._save()
        self._reaction.cancel()
        self._speech.hide()
        self._hover.close_game()
        self._hover.close_settings()
        self._hover.close_toolbar()
        self._root.destroy()
