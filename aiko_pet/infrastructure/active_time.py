"""Separate elapsed life time from active observation/animation time."""

from __future__ import annotations

import ctypes
import sys
import time


def elapsed_uptime_seconds() -> float | None:
    """Suspend-inclusive uptime, unaffected by wall-clock corrections.

    GetTickCount64 includes sleep/hibernation; CLOCK_BOOTTIME does likewise.
    Keep active_uptime_seconds separate for sensory and physics evidence.
    """
    try:
        if sys.platform == "win32":
            function = ctypes.windll.kernel32.GetTickCount64
            function.argtypes = []
            function.restype = ctypes.c_ulonglong
            return int(function()) / 1000.0
        if sys.platform.startswith("linux"):
            return time.clock_gettime(time.CLOCK_BOOTTIME)
    except (AttributeError, OSError, ValueError):
        return None
    return None


def active_uptime_seconds() -> float | None:
    """Windows unbiased interrupt time; Linux CLOCK_MONOTONIC."""
    try:
        if sys.platform == "win32":
            function = ctypes.windll.kernel32.QueryUnbiasedInterruptTime
            function.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
            function.restype = ctypes.c_int
            ticks = ctypes.c_ulonglong()
            if not function(ctypes.byref(ticks)):
                return None
            return int(ticks.value) / 10_000_000.0
        if sys.platform.startswith("linux"):
            return time.clock_gettime(time.CLOCK_MONOTONIC)
    except (AttributeError, OSError, ValueError):
        return None
    return None
