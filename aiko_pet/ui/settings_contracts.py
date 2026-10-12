"""Settings callback capabilities and backwards-compatible snapshot import."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..application.view_models import SettingsSnapshot as SettingsSnapshot


@dataclass(frozen=True, slots=True)
class SettingsActions:
    open_status: Callable[[], None]
    toggle_scale: Callable[[], None]
    set_option: Callable[[str, bool], None]
    forget_rhythm: Callable[[], None]
    reset_toolbar: Callable[[], None]
    center: Callable[[], None]
    quit: Callable[[], None]
    closed: Callable[[], None]
