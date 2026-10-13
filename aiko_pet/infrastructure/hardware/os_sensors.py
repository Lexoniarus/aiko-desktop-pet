"""Windows ctypes and Linux procfs CPU, memory and uptime providers."""

from __future__ import annotations

import ctypes
import sys
from pathlib import Path


def cpu_windows_times() -> tuple[int, int] | None:
    if sys.platform != "win32":
        return None

    class FileTime(ctypes.Structure):
        _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]

        def ticks(self) -> int:
            return (int(self.high) << 32) | int(self.low)

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
        return round(100 * (int(status.total_phys) - int(status.avail_phys)) /
                     int(status.total_phys), 1)
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
            return round(int(function()) / 3_600_000, 2)
        except (AttributeError, OSError, ValueError):
            return None
    if sys.platform.startswith("linux"):
        try:
            return round(float(Path("/proc/uptime").read_text().split()[0]) / 3600, 2)
        except (OSError, ValueError, IndexError):
            return None
    return None
