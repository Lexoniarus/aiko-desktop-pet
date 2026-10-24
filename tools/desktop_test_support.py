"""Real desktop composition with hardware sampling isolated from GUI tests."""

from __future__ import annotations

from aiko_pet.application.session import SavedPetStore
from aiko_pet.application.social_coordinator import SocialContentWorker
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
) -> DesktopPet:
    """Keep real widgets, lifecycle and state, without starting sensor threads."""
    return DesktopPet(
        store=store, activity_monitor=_GuiTestMonitor(), social_worker=social_worker,
    )
