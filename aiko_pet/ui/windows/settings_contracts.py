"""Narrow setting commands; the window never owns application preferences."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ...application.settings import SettingKey


@dataclass(frozen=True, slots=True)
class SettingsActions:
    toggle_scale: Callable[[], None]
    set_option: Callable[[SettingKey, bool], None]
    forget_rhythm: Callable[[], None]
    reset_toolbar: Callable[[], None]
    center: Callable[[], None]
    quit: Callable[[], None]
    closed: Callable[[], None]
