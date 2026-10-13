"""Hardware sampling and smoothing; bounded NVIDIA subprocess in a worker."""

from __future__ import annotations

import subprocess
import sys
import time
from collections import deque

from .metrics import ComputerSnapshot
from .os_sensors import (
    cpu_linux_times, cpu_windows_times, load_percent,
    memory_linux_percent, memory_windows_percent, uptime_hours,
)
from .nvidia import nvidia_executable, parse_nvidia_reading


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
