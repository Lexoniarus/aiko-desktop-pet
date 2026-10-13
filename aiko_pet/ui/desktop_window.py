"""Native transparent Tk desktop window and taskbar geometry.

Window creation, sprite sizing and taskbar grounding belong to this host.
No pet domain, dialogue, hover panel or notification service is imported.
"""

from __future__ import annotations

import sys
import tkinter as tk
from typing import Protocol
from ..desktop.taskbar import locate_primary_taskbar

FRAME_WIDTH = 128
FRAME_HEIGHT = 208
MAGENTA = "#ff00ff"


class WindowSettings(Protocol):
    """Only the mutable placement fields required by a desktop window."""

    x: int | None
    y: int | None
    scale: int
    always_on_top: bool


class DesktopWindow:
    """Own one character window and its taskbar-relative geometry."""

    def __init__(self, settings: WindowSettings) -> None:
        self.settings = settings
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("Aiko Desktop Pet")
        self.root.overrideredirect(True)
        self.background = (
            MAGENTA if sys.platform == "win32" else "#202733"
        )
        self.root.configure(bg=self.background)
        if sys.platform == "win32":
            self.root.wm_attributes("-transparentcolor", MAGENTA)
        self.root.wm_attributes("-topmost", settings.always_on_top)
        self.width = FRAME_WIDTH * settings.scale
        self.height = FRAME_HEIGHT * settings.scale
        self.canvas = tk.Canvas(
            self.root, width=self.width, height=self.height,
            bg=self.background, borderwidth=0, highlightthickness=0,
        )
        self.canvas.pack()
        self.track = locate_primary_taskbar(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        self.placed = False

    def initial_x(self) -> float:
        """Preserve saved location or the original 75% taskbar placement."""
        if self.settings.x is not None:
            return self.settings.x
        return (
            self.track.left
            + round((self.track.right - self.track.left) * 0.75)
        )

    def place_x(self, x: float) -> bool:
        """Ground feet and skip redundant geometry updates."""
        new_x = self.track.clamp_x(x, self.width)
        new_y = self.track.sprite_y(self.settings.scale)
        if (new_x, new_y) == (self.settings.x, self.settings.y) and self.placed:
            return False
        self.settings.x = new_x
        self.settings.y = new_y
        self.root.geometry(f"{self.width}x{self.height}+{new_x}+{new_y}")
        self.placed = True
        return True

    def set_topmost(self, enabled: bool) -> None:
        """Control the character window's stack without touching other views."""
        self.root.wm_attributes("-topmost", enabled)

    def resize(self) -> None:
        """Resize host; frame assets remain the AnimatedPet's responsibility."""
        self.width = FRAME_WIDTH * self.settings.scale
        self.height = FRAME_HEIGHT * self.settings.scale
        self.canvas.config(width=self.width, height=self.height)
        self.placed = False

    def update_track(self) -> bool:
        """Refresh taskbar bounds when Windows reports changed geometry."""
        updated = locate_primary_taskbar(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        if updated == self.track:
            return False
        self.track = updated
        return True
