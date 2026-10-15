"""Application composition shares the caller's pet, mind and clock."""

from __future__ import annotations

import unittest

from aiko_pet.application.active_time import ActiveSessionClock
from aiko_pet.application.activity import ActivityCallbacks
from aiko_pet.application.assembly import assemble_application
from aiko_pet.application.settings import PetSettings
from aiko_pet.pet.mind import PetMind
from aiko_pet.pet.mind.adaptive import AdaptiveRoutine
from aiko_pet.pet.state import PetState
from aiko_pet.telemetry import ComputerSnapshot


class StaticComputer:
    def latest(self) -> ComputerSnapshot:
        return ComputerSnapshot()

    def set_enabled(self, _enabled: bool) -> None:
        pass


class ApplicationAssemblyTests(unittest.TestCase):
    def test_components_reuse_existing_mutable_owners(self) -> None:
        state = PetState()
        settings = PetSettings()
        mind = PetMind()
        adaptive = AdaptiveRoutine()
        services = assemble_application(
            state=state, settings=settings, mind=mind,
            adaptive=adaptive, monitor=StaticComputer(),
            clock=ActiveSessionClock(lambda: 0.0),
            callbacks=ActivityCallbacks(
                read_idle_seconds=lambda: None,
                start_review=lambda _now: None,
                react=lambda _reaction, _duration: None,
                action_until=lambda: 0.0,
                last_spoken=lambda: -1000.0,
            ),
        )
        self.assertIs(services.activity.state, state)
        self.assertIs(services.activity.settings, settings)
        self.assertIs(services.activity.mind, mind)
        self.assertIs(services.activity.adaptive, adaptive)
        self.assertIs(
            services.cursor_observation.attention,
            mind.cursor_attention,
        )
        self.assertIs(
            services.activity.workload_events,
            services.workload_events,
        )
        self.assertIsNotNone(services.router)
