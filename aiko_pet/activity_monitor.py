"""Worker-thread hardware monitoring and immutable cached snapshots."""

from __future__ import annotations

import threading
import time
from typing import Protocol

from .hardware_sampler import HardwareSampler
from .system_metrics import ComputerSnapshot


class Sampler(Protocol):
    def sample(self) -> ComputerSnapshot: ...


class ActivityMonitor:
    """Only worker reads hardware; Tk accesses immutable cached snapshots."""

    def __init__(self, sampler: Sampler | None = None,
                 *, interval_seconds: float = 6.0) -> None:
        self.sampler = sampler or HardwareSampler()
        self.interval_seconds = interval_seconds
        self._snapshot = ComputerSnapshot()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._enabled = threading.Event()
        self._enabled.set()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, daemon=True,
                                        name="AikoHardwareMonitor")
        self._thread.start()

    def _run(self) -> None:
        while not self._stop.is_set():
            if not self._enabled.is_set():
                if self._stop.wait(0.5):
                    break
                continue
            try:
                reading = self.sampler.sample()
            except Exception:
                # Optional hardware instrumentation must never kill Aiko.
                reading = ComputerSnapshot(measured_at=time.monotonic())
            with self._lock:
                if self._enabled.is_set():
                    self._snapshot = reading
            if self._stop.wait(self.interval_seconds):
                break

    def latest(self) -> ComputerSnapshot:
        with self._lock:
            return self._snapshot

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self._enabled.set()
        else:
            self._enabled.clear()
            with self._lock:
                self._snapshot = ComputerSnapshot()

    def stop(self) -> None:
        self._stop.set()
        # The daemon may be in nvidia-smi for at most two seconds. Don't freeze
        # the GUI while shutting down; the daemon will exit on its own.
        if self._thread is not None:
            self._thread.join(timeout=0.05)
