"""Persistent, independently movable settings in the shared Aiko skin."""

from __future__ import annotations

import sys
import time
import tkinter as tk
from functools import partial
from typing import Callable

from ...application.settings import SettingKey
from ...pet.content import GERMAN_TEXT
from ..common.skin import AikoSkin
from ..common.window_drag import WindowDrag, bounded_position
from ..view_models.contracts import SettingsSnapshot
from .settings_contracts import SettingsActions


class SettingsWindow:
    """Own controls and window geometry, not preference values or effects."""

    def __init__(
        self,
        root: tk.Tk,
        x: int,
        y: int,
        *,
        snapshot: Callable[[], SettingsSnapshot],
        actions: SettingsActions,
        always_on_top: bool,
        skin: AikoSkin | None = None,
        position: tuple[int, int] | None = None,
    ) -> None:
        self._snapshot = snapshot
        self._actions = actions
        self._closed = False
        self._last_key = float("-inf")
        self.position = position
        self.skin = skin if skin is not None else AikoSkin(root)
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.title(GERMAN_TEXT.format("settings.window_title"))
        self.window.configure(bg=self.skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.bind("<Control-q>", lambda _event: actions.quit())
        self.window.bind("<KeyPress>", self._key_pressed, add="+")
        outer = self.skin.frame(self.window)
        outer.pack(fill="both", expand=True, padx=3, pady=3)
        self.header = self.skin.header(outer, GERMAN_TEXT.format("settings.header"))
        self.header.pack(fill="x")
        self._drag = WindowDrag(
            self.window,
            self.header,
            dropped=self._remember_position,
        )
        body = tk.Frame(outer, bg=self.skin.background)
        body.pack(fill="both", expand=True, padx=10, pady=5)
        self.values: dict[SettingKey, tk.BooleanVar] = {}
        self.checkbuttons: dict[SettingKey, tk.Checkbutton] = {}
        self._heading(body, GERMAN_TEXT.format("settings.appearance_heading"))
        self.scale_button = self.skin.button(
            body,
            "",
            partial(self._invoke, actions.toggle_scale),
            size="wide",
        )
        self.scale_button.pack(anchor="w", pady=2)
        self._option(
            body, "always_on_top", GERMAN_TEXT.format("settings.always_on_top")
        )
        self._option(body, "auto_walk", GERMAN_TEXT.format("settings.auto_walk"))
        self._option(
            body, "follow_cursor", GERMAN_TEXT.format("settings.follow_cursor")
        )
        self._heading(body, GERMAN_TEXT.format("settings.behaviour_heading"))
        self._option(body, "auto_routine", GERMAN_TEXT.format("settings.auto_routine"))
        self._option(
            body, "spontaneous_talk", GERMAN_TEXT.format("settings.spontaneous_talk")
        )
        self._option(
            body, "observe_computer", GERMAN_TEXT.format("settings.observe_computer")
        )
        self._option(body, "learn_rhythm", GERMAN_TEXT.format("settings.learn_rhythm"))
        self._heading(body, GERMAN_TEXT.format("settings.local_heading"))
        self.forget_button = self.skin.button(
            body,
            GERMAN_TEXT.format("settings.forget_rhythm"),
            partial(self._invoke, actions.forget_rhythm),
            size="wide",
        )
        self.forget_button.pack(anchor="w", pady=2)
        positions = tk.Frame(body, bg=self.skin.background)
        positions.pack(fill="x", pady=2)
        self.reset_button = self.skin.button(
            positions,
            GERMAN_TEXT.format("settings.reset_toolbar"),
            partial(self._invoke, actions.reset_toolbar),
            size="wide",
        )
        self.reset_button.pack(side="left", padx=(0, 4))
        self.center_button = self.skin.button(
            positions,
            GERMAN_TEXT.format("settings.center"),
            partial(self._invoke, actions.center),
            size="wide",
        )
        self.center_button.pack(side="left")
        footer = tk.Frame(outer, bg=self.skin.background)
        footer.pack(fill="x", padx=10, pady=(3, 8))
        self.quit_button = self.skin.button(
            footer, GERMAN_TEXT.format("ui.quit"), actions.quit
        )
        self.quit_button.pack(side="left")
        self.close_button = self.skin.button(
            footer, GERMAN_TEXT.format("ui.close"), self.close
        )
        self.close_button.pack(side="right")
        self.refresh()
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        target = position if position is not None else (x - width, y)
        self.position = bounded_position(
            *target,
            width,
            height,
            root.winfo_screenwidth(),
            root.winfo_screenheight(),
        )
        self.window.geometry(f"+{self.position[0]}+{self.position[1]}")
        self.window.deiconify()

    def _heading(self, parent: tk.Widget, text: str) -> None:
        tk.Label(
            parent,
            text=text,
            bg=self.skin.background,
            fg=self.skin.muted,
            font=(self.skin.font, 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(7, 2))

    def _option(self, parent: tk.Widget, key: SettingKey, text: str) -> None:
        variable = tk.BooleanVar(master=self.window)
        self.values[key] = variable
        button = tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            command=partial(self._apply_setting, key, variable),
            bg=self.skin.background,
            fg=self.skin.text,
            activebackground=self.skin.panel,
            activeforeground=self.skin.text,
            selectcolor=self.skin.panel,
            font=(self.skin.font, 9),
            anchor="w",
            bd=0,
            highlightthickness=1,
            pady=3,
            highlightbackground=self.skin.background,
            highlightcolor=self.skin.accent,
            cursor="hand2",
        )
        button.pack(fill="x")
        self.checkbuttons[key] = button

    def _apply_setting(self, name: SettingKey, variable: tk.BooleanVar) -> None:
        self._actions.set_option(name, variable.get())
        self.refresh()

    def _invoke(self, command: Callable[[], None]) -> None:
        command()
        self.refresh()

    def refresh(self) -> None:
        """Reflect authoritative preferences without firing commands."""
        if self._closed:
            return
        view = self._snapshot()
        for key, variable in self.values.items():
            value = view.value(key)
            if variable.get() != value:
                variable.set(value)
        self.scale_button.configure(
            text=GERMAN_TEXT.format(
                "settings.scale",
                scale=str(view.scale),
            )
        )

    def _remember_position(self, x: int, y: int) -> None:
        self.position = (x, y)

    def _key_pressed(self, _event: tk.Event) -> None:
        self._last_key = time.monotonic()

    @property
    def dragging(self) -> bool:
        return self._drag.dragging

    def contains_pointer(self, px: int, py: int) -> bool:
        if self._closed or not self.window.winfo_ismapped():
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (
            x <= px < x + self.window.winfo_width()
            and y <= py < y + self.window.winfo_height()
        )

    def interacting(self, px: int, py: int, now: float) -> bool:
        return not self._closed and (
            self.dragging or self.contains_pointer(px, py) or now - self._last_key < 2.0
        )

    def focus(self) -> None:
        """Only explicit user requests activate a persistent settings window."""
        if not self._closed:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_set()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self.window.winfo_ismapped():
            self.position = (
                self.window.winfo_rootx(),
                self.window.winfo_rooty(),
            )
        self._drag.close()
        self.window.destroy()
        self._actions.closed()
