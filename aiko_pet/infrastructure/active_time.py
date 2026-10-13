"""Platform uptime for session simulation, excluding sleep and hibernation."""

from __future__ import annotations

import ctypes
import sys
import time


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
