"""Nonmodal VN settings, immediate preferences and embedded central Credits."""

from __future__ import annotations

import sys
import time
import tkinter as tk
from functools import partial
from tkinter import ttk
from typing import Callable

from ...application.horoscope_models import ZODIAC_SIGNS
from ...application.settings import SettingKey
from ...pet.content import GERMAN_TEXT
from ..common.image_button import ImageButton
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_drag import WindowDrag, bounded_position
from ..view_models.contracts import SettingsSnapshot
from ..view_models.credits import CreditsSnapshot
from .credits_panel import CreditsPanel
from .settings_contracts import SettingsActions


class SettingsWindow:
    APPEARANCE: tuple[SettingKey, ...] = ("always_on_top", "auto_walk", "follow_cursor")
    BEHAVIOUR: tuple[SettingKey, ...] = (
        "auto_routine",
        "spontaneous_talk",
        "observe_computer",
        "learn_rhythm",
        "online_social",
    )
    SECTIONS = ("appearance", "behaviour", "local", "credits")

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
        credits_snapshot: Callable[[], CreditsSnapshot] = CreditsSnapshot,
    ) -> None:
        self._snapshot, self._actions = snapshot, actions
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
        self.window.bind("<Escape>", lambda _e: self.close())
        self.window.bind("<Control-q>", lambda _e: actions.quit())
        self.window.bind("<KeyPress>", self._key_pressed, add="+")
        outer = self.skin.frame(self.window)
        outer.pack(fill="both", expand=True, padx=1, pady=1)
        self.header = self.skin.header(outer, GERMAN_TEXT.format("settings.header"))
        self.header.pack(fill="x")
        self._drag = WindowDrag(
            self.window, self.header, dropped=self._remember_position
        )
        footer = tk.Frame(outer, bg=self.skin.background)
        footer.pack(side="bottom", fill="x", padx=10, pady=8)
        self.quit_button = self.skin.button(
            footer, GERMAN_TEXT.format("ui.quit"), actions.quit
        )
        self.quit_button.pack(side="left")
        self.close_button = self.skin.button(
            footer, GERMAN_TEXT.format("ui.close"), self.close
        )
        self.close_button.pack(side="right")
        body = tk.Frame(outer, bg=self.skin.background)
        body.pack(fill="both", expand=True, padx=10, pady=8)
        navigation = tk.Frame(body, bg=self.skin.background)
        navigation.pack(side="left", fill="y", padx=(0, 12))
        self._scroll = ScrollRegion(
            body,
            self.skin,
            width=500,
            height=min(484, max(220, root.winfo_screenheight() - 180)),
        )
        self._scroll.frame.pack(side="right", fill="both", expand=True)
        self._pages = {
            section: tk.Frame(self._scroll.body, bg=self.skin.background)
            for section in self.SECTIONS
        }
        self.navigation: dict[str, ImageButton] = {}
        for index, section in enumerate(self.SECTIONS):
            key = (
                "vn.credits" if section == "credits" else f"settings.{section}_heading"
            )
            button = self.skin.button(
                navigation,
                GERMAN_TEXT.format(key),
                partial(self.select_section, section),
            )
            button.pack(pady=3)
            for keypress, nav_index in (
                ("Down", (index + 1) % 4),
                ("Right", (index + 1) % 4),
                ("Up", (index - 1) % 4),
                ("Left", (index - 1) % 4),
                ("Home", 0),
                ("End", 3),
            ):
                button.bind(f"<{keypress}>", partial(self._navigate, nav_index))
            self.navigation[section] = button
        self.values: dict[SettingKey, tk.BooleanVar] = {}
        self.checkbuttons: dict[SettingKey, tk.Checkbutton] = {}
        self._state_labels: dict[SettingKey, tk.Label] = {}
        self.scale_buttons: dict[int, ImageButton] = {}
        scales = tk.Frame(self._pages["appearance"], bg=self.skin.background)
        scales.pack(fill="x", pady=6)
        for scale in (1, 2):
            button = self.skin.button(
                scales, f"{scale}×", partial(self._choose_scale, scale)
            )
            button.pack(side="left", padx=2)
            self.scale_buttons[scale] = button
        for key in self.APPEARANCE:
            self._option(self._pages["appearance"], key)
        for key in self.BEHAVIOUR:
            self._option(self._pages["behaviour"], key)
        zodiac = self._pages["behaviour"]
        tk.Label(
            zodiac,
            text=GERMAN_TEXT.format("settings.zodiac_sign"),
            bg=self.skin.background,
            fg=self.skin.text,
            font=(self.skin.font, 10),
        ).pack(anchor="w", pady=(8, 3))
        self._signs = (None, *ZODIAC_SIGNS)
        self._sign_labels = tuple(
            GERMAN_TEXT.format(f"social.zodiac.{s or 'none'}") for s in self._signs
        )
        self.zodiac_value = tk.StringVar(master=self.window)
        self.zodiac_choice = ttk.Combobox(
            zodiac,
            textvariable=self.zodiac_value,
            values=self._sign_labels,
            state="readonly",
            width=28,
            font=(self.skin.font, 10),
        )
        self.zodiac_choice.pack(anchor="w", pady=(0, 8))
        self.zodiac_choice.bind("<<ComboboxSelected>>", self._choose_zodiac)
        tk.Label(
            zodiac,
            text=GERMAN_TEXT.format("settings.horoscope_note"),
            bg=self.skin.background,
            fg=self.skin.muted,
            wraplength=340,
            justify="left",
            font=(self.skin.font, 8),
        ).pack(anchor="w", pady=(0, 8))
        local = self._pages["local"]
        self.forget_button = self.skin.button(
            local,
            GERMAN_TEXT.format("settings.forget_rhythm"),
            partial(self._invoke, actions.forget_rhythm),
            size="wide",
        )
        self.forget_button.pack(anchor="w", pady=5)
        self.reset_button = self.skin.button(
            local,
            GERMAN_TEXT.format("settings.reset_toolbar"),
            partial(self._invoke, actions.reset_toolbar),
            size="wide",
        )
        self.reset_button.pack(anchor="w", pady=5)
        self.center_button = self.skin.button(
            local,
            GERMAN_TEXT.format("settings.center"),
            partial(self._invoke, actions.center),
            size="wide",
        )
        self.center_button.pack(anchor="w", pady=5)
        self.credits = CreditsPanel(self._pages["credits"], self.skin, credits_snapshot)
        self.credits.frame.pack(fill="both", expand=True)
        self._section = "appearance"
        self.select_section("appearance")
        self.refresh()
        self.window.update_idletasks()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        target = position if position is not None else (x - width, y)
        self.position = bounded_position(
            *target, width, height, root.winfo_screenwidth(), root.winfo_screenheight()
        )
        self.window.geometry(f"+{self.position[0]}+{self.position[1]}")
        self.window.deiconify()

    def select_section(self, section: str) -> None:
        if section not in self._pages or self._closed:
            return
        self._section = section
        for key, page in self._pages.items():
            if key == section:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
            self.navigation[key].set_selected(key == section)
        self._scroll.canvas.yview_moveto(0)
        self._scroll.adopt()
        self.refresh_credits()

    def _navigate(self, index: int, _event: tk.Event) -> str:
        section = self.SECTIONS[index]
        self.select_section(section)
        self.navigation[section].focus_set()
        return "break"

    def _option(self, parent: tk.Misc, key: SettingKey) -> None:
        row = tk.Frame(parent, bg=self.skin.background)
        row.pack(fill="x", pady=5)
        variable = tk.BooleanVar(master=self.window)
        self.values[key] = variable
        self._state_labels[key] = tk.Label(
            row,
            bg=self.skin.background,
            fg=self.skin.muted,
            font=(self.skin.font, 9),
            width=4,
        )
        self._state_labels[key].pack(side="right")
        button = tk.Checkbutton(
            row,
            text=GERMAN_TEXT.format(f"settings.{key}"),
            variable=variable,
            command=partial(self._apply_setting, key, variable),
            bg=self.skin.background,
            fg=self.skin.text,
            activebackground=self.skin.panel,
            selectcolor=self.skin.panel,
            font=(self.skin.font, 10),
            anchor="w",
            bd=0,
            highlightthickness=2,
            highlightbackground=self.skin.background,
            highlightcolor=self.skin.accent,
            wraplength=390,
            justify="left",
            takefocus=True,
        )
        button.pack(side="left", fill="x", expand=True)
        self.checkbuttons[key] = button

    def _choose_zodiac(self, _event: tk.Event) -> None:
        index = self._sign_labels.index(self.zodiac_value.get())
        self._actions.set_zodiac(self._signs[index])
        self.refresh()

    def _choose_scale(self, scale: int) -> None:
        if self._snapshot().scale != scale:
            self._invoke(self._actions.toggle_scale)

    def _apply_setting(self, name: SettingKey, variable: tk.BooleanVar) -> None:
        self._actions.set_option(name, variable.get())
        self.refresh()

    def _invoke(self, command: Callable[[], None]) -> None:
        command()
        self.refresh()

    def refresh_credits(self) -> None:
        if not self._closed and self._section == "credits":
            self.credits.refresh()

    def refresh(self) -> None:
        if self._closed:
            return
        view = self._snapshot()
        self.zodiac_value.set(self._sign_labels[self._signs.index(view.zodiac_sign)])
        for key, variable in self.values.items():
            value = view.value(key)
            if variable.get() != value:
                variable.set(value)
            self._state_labels[key].configure(
                text=GERMAN_TEXT.format(
                    "vn.settings.on" if value else "vn.settings.off"
                )
            )
        for scale, button in self.scale_buttons.items():
            button.set_selected(view.scale == scale)
        self.refresh_credits()

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
