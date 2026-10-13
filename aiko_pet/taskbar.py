"""Legacy taskbar exports; desktop owns native discovery and geometry."""

from __future__ import annotations

import sys as sys

from .desktop.geometry import (
    FOOT_BASELINE as FOOT_BASELINE,
    TaskbarTrack as TaskbarTrack,
)
from .desktop.taskbar import (
    ABE_BOTTOM as ABE_BOTTOM,
    FALLBACK_TASKBAR_HEIGHT as FALLBACK_TASKBAR_HEIGHT,
    choose_track as choose_track,
    locate_primary_taskbar as locate_primary_taskbar,
    _windows_desktop_geometry as _windows_desktop_geometry,
)
