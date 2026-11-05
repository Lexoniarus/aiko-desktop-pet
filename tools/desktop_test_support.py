"""Real desktop composition with hardware sampling isolated from GUI tests."""

from __future__ import annotations

import tkinter as tk
import unittest

from aiko_pet.application.session import SavedPetStore
from aiko_pet.application.social_content import PreparedSocialContent
from aiko_pet.application.social_fetch import SocialContentWorker
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.hardware.monitor import ActivityMonitor
from aiko_pet.telemetry import ComputerSnapshot


class _IdleSampler:
    def sample(self) -> ComputerSnapshot:
        return ComputerSnapshot()


class _GuiTestMonitor(ActivityMonitor):
    def __init__(self) -> None:
        super().__init__(_IdleSampler())

    def start(self) -> None:
        """GUI assertions inject readings; worker behavior has separate tests."""


def create_test_desktop(
    *, store: SavedPetStore, social_worker: SocialContentWorker | None = None,
    local_social_content: tuple[PreparedSocialContent, ...] = (),
) -> DesktopPet:
    """Keep real widgets, lifecycle and state, without starting sensor threads."""
    return DesktopPet(
        store=store, activity_monitor=_GuiTestMonitor(), social_worker=social_worker,
        local_social_content=local_social_content,
    )


def destroy_test_root(root: tk.Tk) -> None:
    """Flush queued theme/geometry idle work before deleting its interpreter."""
    try:
        root.update_idletasks()
    finally:
        root.destroy()


def require_tk_display() -> None:
    """Probe native Tk without leaving a destroyed interpreter's idle events."""
    try:
        root = tk.Tk()
    except tk.TclError as error:
        raise unittest.SkipTest("Native Tk display required") from error
    destroy_test_root(root)
