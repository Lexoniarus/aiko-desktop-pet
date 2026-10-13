"""Compatibility imports for hardware monitoring; implementations are split.

The shared sys/ctypes/subprocess modules remain available to existing tests.
"""

from __future__ import annotations

import ctypes as ctypes
import subprocess as subprocess
import sys as sys

from .activity_monitor import (
    ActivityMonitor as ActivityMonitor,
    Sampler as Sampler,
)
from .hardware_sampler import HardwareSampler as HardwareSampler
from .system_metrics import (
    ComputerSnapshot as ComputerSnapshot,
    percent_label as percent_label,
    workload_description as workload_description,
    workload_intensity as workload_intensity,
)
from .system_nvidia import (
    nvidia_executable as nvidia_executable,
    parse_nvidia_reading as parse_nvidia_reading,
)
from .system_os import (
    cpu_linux_times as cpu_linux_times,
    cpu_windows_times as cpu_windows_times,
    load_percent as load_percent,
    memory_linux_percent as memory_linux_percent,
    memory_windows_percent as memory_windows_percent,
    uptime_hours as uptime_hours,
)
