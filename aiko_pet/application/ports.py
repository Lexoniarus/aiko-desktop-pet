"""Application-owned capabilities for reading observed hardware activity.

Providers supply immutable telemetry through structural typing; application
logic never depends on a monitor thread or a concrete OS hardware adapter.
"""

from __future__ import annotations

from typing import Protocol

from ..telemetry import ComputerSnapshot


class ComputerReadings(Protocol):
    def latest(self) -> ComputerSnapshot: ...


class ComputerObservation(ComputerReadings, Protocol):
    def set_enabled(self, enabled: bool) -> None: ...
