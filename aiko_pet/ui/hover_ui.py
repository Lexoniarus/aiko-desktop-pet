"""Own hover, status and settings windows separately from animated Aiko.

The desktop shell supplies small presentation snapshots and action callbacks.
This controller handles only Tk window lifecycle, pointer tracking and layout.
"""

from __future__ import annotations

import time
import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from .action_toolbar import ActionToolbar
from .hover_contracts import HoverActions, HoverAnchor, HoverSnapshot
from .settings_contracts import SettingsActions, SettingsSnapshot
from .settings_popup import SettingsPopup
from .status_contracts import StatusActions, StatusSnapshot
from .status_panel import StatusPanel


@dataclass(frozen=True, slots=True)
class HoverUiPorts:
    """Only operations the desktop host grants to its independent UI."""

    hover_snapshot: Callable[[], HoverSnapshot]
    status_snapshot: Callable[[], StatusSnapshot]
    settings_snapshot: Callable[[], SettingsSnapshot]
    anchor: Callable[[], HoverAnchor]
    care: Callable[[str], None]
    open_sprite_hover: Callable[[], None]
    record_contact: Callable[[float], None]
    save_position: Callable[[int | None, int | None], None]
    set_option: Callable[[str, bool], None]
    toggle_scale: Callable[[], None]
    forget_rhythm: Callable[[], None]
    reset_toolbar: Callable[[], None]
    center: Callable[[], None]
    quit: Callable[[], None]
    move_speech: Callable[[], None]
    restore_stack: Callable[[], bool]
    always_on_top: Callable[[], bool]


class HoverUi:
    """Independent owner of the hover panel and its accessory windows."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas, ports: HoverUiPorts,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self._ports = ports
        self.toolbar: ActionToolbar | None = None
        self.status_panel: StatusPanel | None = None
        self.settings_popup: SettingsPopup | None = None
        self.last_hover = -100.0

    @property
    def menu_is_open(self) -> bool:
        return self.settings_popup is not None

    def show_toolbar(self) -> None:
        if self.toolbar is None:
            self.toolbar = ActionToolbar(
                self.root,
                snapshot=self._ports.hover_snapshot,
                anchor=self._ports.anchor,
                actions=HoverActions(
                    interact=self._ports.care,
                    open_status=self.open_status,
                    open_settings=self.toggle_settings,
                    save_position=self._ports.save_position,
                    move_speech=self._ports.move_speech,
                    restore_stack=self._ports.restore_stack,
                ),
                always_on_top=self._ports.always_on_top(),
            )
        self.toolbar.show()

    def _toolbar_top(self) -> int | None:
        return (
            self.toolbar.window.winfo_rooty()
            if self.toolbar is not None else None
        )

    def _settings_closed(self) -> None:
        self.settings_popup = None
        self.last_hover = time.monotonic()

    def toggle_settings(self, x: int, y: int) -> None:
        if self.settings_popup is not None:
            self.settings_popup.close()
            return
        self._ports.open_sprite_hover()
        self.settings_popup = SettingsPopup(
            self.root, x, y,
            snapshot=self._ports.settings_snapshot(),
            actions=SettingsActions(
                open_status=self.open_status,
                toggle_scale=self._ports.toggle_scale,
                set_option=self._ports.set_option,
                forget_rhythm=self._ports.forget_rhythm,
                reset_toolbar=self._ports.reset_toolbar,
                center=self._ports.center,
                quit=self._ports.quit,
                closed=self._settings_closed,
            ),
            toolbar_y=self._toolbar_top,
            always_on_top=self._ports.always_on_top(),
        )
        self._ports.restore_stack()

    def _status_closed(self) -> None:
        self.status_panel = None

    def open_status(self) -> None:
        if self.status_panel is not None:
            self._ports.restore_stack()
            return
        self.status_panel = StatusPanel(
            self.root,
            snapshot=self._ports.status_snapshot,
            anchor=self._ports.anchor,
            actions=StatusActions(
                interact=self._ports.care,
                quit=self._ports.quit,
                closed=self._status_closed,
            ),
            always_on_top=self._ports.always_on_top(),
        )
        self._ports.restore_stack()

    def refresh_status(self) -> None:
        if self.status_panel is not None:
            self.status_panel.refresh()

    def pointer_inside(self, x: int, y: int) -> bool:
        widget = self.root.winfo_containing(x, y)
        over_sprite = widget is self.root or widget is self.canvas
        toolbar = self.toolbar
        over_toolbar = (
            toolbar is not None
            and (
                toolbar.contains_pointer(x, y)
                or toolbar.contains_bridge(x, y)
            )
        )
        return bool(over_sprite or over_toolbar)

    def dismiss_outside(self, x: int, y: int) -> None:
        toolbar = self.toolbar
        if toolbar is not None and toolbar._dragging:
            return
        over_ui = self.pointer_inside(x, y)
        popup = self.settings_popup
        over_popup = popup is not None and popup.contains_pointer(x, y)
        if popup is not None and not over_popup and not over_ui:
            popup.close()
        if (
            toolbar is not None and toolbar.visible
            and not (over_ui or over_popup)
        ):
            toolbar.hide()

    def refresh_hover(self, now: float) -> None:
        toolbar = self.toolbar
        if toolbar is not None and toolbar._dragging:
            self.last_hover = now
            return
        if self.settings_popup is not None:
            return
        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        if self.pointer_inside(x, y):
            self.last_hover = now
            widget = self.root.winfo_containing(x, y)
            if widget in (self.root, self.canvas) and (
                toolbar is None or not toolbar.visible
            ):
                self._ports.open_sprite_hover()
            self._ports.record_contact(now)
        elif toolbar is not None and toolbar.visible and (
            now - self.last_hover >= (
                2.0 if self._ports.anchor().pinned_x is not None else 0.9
            )
        ):
            toolbar.hide()

    def close_toolbar(self) -> None:
        if self.toolbar is not None:
            self.toolbar.close()
            self.toolbar = None
