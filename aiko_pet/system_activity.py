"""Small offline Windows hardware sampler; never runs subprocesses on Tk's thread.

CPU and physical memory come from the Windows API. NVIDIA GPU utilization is
optional and read from nvidia-smi; other GPUs simply report 'unavailable'.
Linux procfs is used for development/tests. No process names or private data
are read, and the samples are not written to the save file.
"""

from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ComputerSnapshot:
    cpu: float | None = None
    gpu: float | None = None
    ram: float | None = None
    gpu_memory: float | None = None
    uptime_hours: float | None = None
    measured_at: float = 0.0

    def is_busy(self) -> bool:
        return (workload_intensity(self) or 0.0) >= 0.70


def workload_intensity(snapshot: ComputerSnapshot) -> float | None:
    """Estimate *effort*, not task identity or memory allocation alone.

    CPU/GPU utilization carry the main signal; high RAM/VRAM occupancy adds
    moderate pressure. Unknown sensors never turn into fabricated 0% loads.
    """
    if all(value is None for value in (snapshot.cpu, snapshot.gpu, snapshot.ram)):
        return None
    cpu = max(0.0, min(1.0, (snapshot.cpu or 0) / 100))
    gpu = max(0.0, min(1.0, (snapshot.gpu or 0) / 100))
    work = max(cpu, gpu) + 0.08 * min(cpu, gpu)
    if snapshot.ram is not None and snapshot.ram > 82:
        work += 0.12 * min(1.0, (snapshot.ram - 82) / 18)
    if snapshot.gpu_memory is not None and snapshot.gpu_memory > 94:
        work += 0.035 * min(1.0, (snapshot.gpu_memory - 94) / 6)
    return round(min(1.0, work), 3)


def workload_description(snapshot: ComputerSnapshot) -> str:
    """Readable private effort, not a recitation of component names."""
    effort = workload_intensity(snapshot)
    if snapshot.measured_at <= 0 or effort is None:
        return "Ich orientiere mich noch ..."
    if effort >= 0.9:
        return "Ich bin gerade voll konzentriert."
    if effort >= 0.7:
        return "Ich habe ordentlich zu tun."
    if effort >= 0.36:
        return "Ich bin beschäftigt."
    return "Ich habe gerade etwas Ruhe."


def percent_label(number: float | None) -> str:
    return "–" if number is None else f"{max(0, min(100, round(number)))} %"


def cpu_windows_times() -> tuple[int, int] | None:
    if sys.platform != "win32":
        return None

    class FileTime(ctypes.Structure):
        _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]

        def ticks(self) -> int:
            return (self.high << 32) | self.low

    idle, kernel, user = FileTime(), FileTime(), FileTime()
    try:
        success = ctypes.windll.kernel32.GetSystemTimes(
            ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user),
        )
        if not success:
            return None
        # Win32 kernel time already includes idle time.
        return idle.ticks(), kernel.ticks() + user.ticks()
    except (AttributeError, OSError, ValueError):
        return None


def cpu_linux_times() -> tuple[int, int] | None:
    try:
        first = Path("/proc/stat").read_text(encoding="ascii").splitlines()[0]
        parts = first.split()
        if parts[0] != "cpu" or len(parts) < 5:
            return None
        values = [int(v) for v in parts[1:9]]
        return values[3] + (values[4] if len(values) >= 5 else 0), sum(values)
    except (OSError, ValueError, IndexError):
        return None


def load_percent(previous: tuple[int, int] | None,
                 current: tuple[int, int] | None) -> float | None:
    if previous is None or current is None:
        return None
    idle = current[0] - previous[0]
    total = current[1] - previous[1]
    if total <= 0 or idle < 0:
        return None
    return round(min(100.0, max(0.0, 100.0 * (1.0 - idle / total))), 1)


def memory_windows_percent() -> float | None:
    if sys.platform != "win32":
        return None

    class MemoryStatus(ctypes.Structure):
        _fields_ = [
            ("length", ctypes.c_uint32),
            ("memory_load", ctypes.c_uint32),
            ("total_phys", ctypes.c_uint64),
            ("avail_phys", ctypes.c_uint64),
            ("total_page", ctypes.c_uint64),
            ("avail_page", ctypes.c_uint64),
            ("total_virtual", ctypes.c_uint64),
            ("avail_virtual", ctypes.c_uint64),
            ("avail_extended", ctypes.c_uint64),
        ]

    status = MemoryStatus()
    status.length = ctypes.sizeof(status)
    try:
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None
        if not status.total_phys:
            return None
        return round(100 * (status.total_phys - status.avail_phys) /
                     status.total_phys, 1)
    except (AttributeError, OSError, ValueError):
        return None


def memory_linux_percent() -> float | None:
    try:
        data = Path("/proc/meminfo").read_text(encoding="ascii")
        rows = {}
        for line in data.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                rows[key] = int(value.strip().split()[0])
        if rows["MemTotal"] <= 0:
            return None
        return round(100 * (1 - rows["MemAvailable"] / rows["MemTotal"]), 1)
    except (OSError, ValueError, KeyError, IndexError):
        return None


def uptime_hours() -> float | None:
    if sys.platform == "win32":
        try:
            # milliseconds since Windows boot; does not inspect user activity.
            function = ctypes.windll.kernel32.GetTickCount64
            function.restype = ctypes.c_uint64
            return round(function() / 3_600_000, 2)
        except (AttributeError, OSError, ValueError):
            return None
    if sys.platform.startswith("linux"):
        try:
            return round(float(Path("/proc/uptime").read_text().split()[0]) / 3600, 2)
        except (OSError, ValueError, IndexError):
            return None
    return None


def nvidia_executable() -> str | None:
    found = shutil.which("nvidia-smi")
    if found:
        return found
    if sys.platform == "win32":
        for base in (
            os.environ.get("WINDIR", r"C:\Windows"),
            os.environ.get("ProgramFiles", r"C:\Program Files"),
        ):
            parent = Path(base)
            for subpath in (
                "System32/nvidia-smi.exe",
                "NVIDIA Corporation/NVSMI/nvidia-smi.exe",
            ):
                candidate = parent / subpath
                if candidate.is_file():
                    return str(candidate)
    return None


def parse_nvidia_reading(output: str) -> tuple[float | None, float | None]:
    """Select highest utilization on multi-GPU machines; no silent fake zeros."""
    readings: list[tuple[float, float | None]] = []
    for line in output.splitlines():
        fields = [item.strip() for item in line.split(",")]
        if len(fields) < 3:
            continue
        try:
            utilization = float(fields[0])
            used = float(fields[1])
            total = float(fields[2])
        except ValueError:
            continue
        if not 0 <= utilization <= 100 or used < 0 or total < 0:
            continue
        memory = min(100, 100 * used / total) if total > 0 else None
        readings.append((utilization, memory))
    if not readings:
        return None, None
    return max(readings, key=lambda item: item[0])


class HardwareSampler:
    """Collect inexpensive OS metrics plus optional bounded NVIDIA subprocess."""

    def __init__(self) -> None:
        self._previous: tuple[int, int] | None = None
        self._gpu_command = nvidia_executable()
        self._recent_cpu: deque[float] = deque(maxlen=2)
        self._recent_gpu: deque[float] = deque(maxlen=2)

    def sample(self) -> ComputerSnapshot:
        if sys.platform == "win32":
            current = cpu_windows_times()
            ram = memory_windows_percent()
        elif sys.platform.startswith("linux"):
            current = cpu_linux_times()
            ram = memory_linux_percent()
        else:
            current, ram = None, None
        cpu = load_percent(self._previous, current)
        self._previous = current
        if cpu is not None:
            self._recent_cpu.append(cpu)
        gpu: float | None = None
        gpu_memory: float | None = None
        if self._gpu_command:
            try:
                result = subprocess.run(
                    [self._gpu_command,
                     "--query-gpu=utilization.gpu,memory.used,memory.total",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=2.0, check=False,
                    creationflags=(
                        int(getattr(subprocess, "CREATE_NO_WINDOW", 0))
                        if sys.platform == "win32" else 0
                    ),
                )
                if result.returncode == 0:
                    gpu, gpu_memory = parse_nvidia_reading(result.stdout)
            except (OSError, subprocess.SubprocessError):
                pass
        if gpu is not None:
            self._recent_gpu.append(gpu)
        return ComputerSnapshot(
            cpu=round(sum(self._recent_cpu) / len(self._recent_cpu), 1)
            if self._recent_cpu else None,
            gpu=round(sum(self._recent_gpu) / len(self._recent_gpu), 1)
            if gpu is not None else None,
            ram=ram,
            gpu_memory=gpu_memory,
            uptime_hours=uptime_hours(),
            measured_at=time.monotonic(),
        )


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
