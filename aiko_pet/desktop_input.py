"""Legacy global-click imports, implemented by desktop.global_input."""

from __future__ import annotations

import ctypes as ctypes
import sys as sys

from .desktop.global_input import (
    VK_LBUTTON as VK_LBUTTON,
    VK_RBUTTON as VK_RBUTTON,
    GlobalMouseClicks as GlobalMouseClicks,
    idle_seconds_windows as idle_seconds_windows,
)
