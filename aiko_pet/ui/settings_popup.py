"""Tk settings popover with narrow actions rather than DesktopPet access."""

from __future__ import annotations

import sys
import tkinter as tk
from functools import partial
from typing import Callable, Literal

from ..application.settings import SettingKey

from .settings_contracts import SettingsActions, SettingsSnapshot


class SettingsPopup:
    """A normal popover that owns only its Tk controls and local geometry."""

    def __init__(
        self, root: tk.Tk, x: int, y: int, *,
        snapshot: SettingsSnapshot, actions: SettingsActions,
        toolbar_y: Callable[[], int | None], always_on_top: bool,
    ) -> None:
        self.root = root
        self._actions = actions
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg="#1b2635")
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        frame = tk.Frame(
            self.window, bg="#233042", highlightbackground="#728ba5",
            highlightthickness=1,
        )
        frame.pack()
        header = tk.Frame(frame, bg="#233042")
        header.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(
            header, text="AIKO · EINSTELLUNGEN", bg="#233042",
            fg="#b0dff5", font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(2, 16))
        self._button(header, "×", self.close, side="right")
        self.values: dict[str, tk.BooleanVar] = {}
        self._button(
            frame, "Status und Aktionen ...",
            partial(self._invoke, actions.open_status),
        )
        self._button(
            frame,
            "Größe: 2× (Pixel)" if snapshot.scale == 1
            else "Größe: 1× (klein)",
            partial(self._invoke, actions.toggle_scale),
        )
        labels: tuple[tuple[SettingKey, str], ...] = (
            ("always_on_top", "Immer im Vordergrund"),
            ("auto_walk", "An der Taskleiste laufen"),
            ("auto_routine", "Automatischer Tagesrhythmus"),
            ("follow_cursor", "Maus beobachten"),
            ("spontaneous_talk", "Von selbst sprechen"),
            ("observe_computer", "Rechnerauslastung beobachten"),
            ("learn_rhythm", "Meinen Rhythmus kennenlernen"),
        )
        for key, label in labels:
            variable = tk.BooleanVar(value=snapshot.value(key))
            self.values[key] = variable
            tk.Checkbutton(
                frame, text=label, variable=variable,
                command=partial(self._apply_setting, key, variable),
                bg="#233042", fg="#edf5fe", selectcolor="#314158",
                activebackground="#314158", activeforeground="#ffffff",
                anchor="w", padx=9, pady=4, font=("Segoe UI", 9),
                bd=0, highlightthickness=0,
            ).pack(fill="x", padx=7)
        for label, command in (
            ("Gelerntes Tagesmuster löschen", actions.forget_rhythm),
            ("Leiste wieder neben Aiko", actions.reset_toolbar),
            ("Zur Taskleistenmitte", actions.center),
        ):
            self._button(frame, label, partial(self._invoke, command))
        self._button(frame, "Beenden", self._quit)
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        target_x = max(0, min(int(x - width), screen_width - width))
        target_y = int(y)
        if target_y + height + 8 > screen_height:
            top = toolbar_y()
            target_y = (
                top - height - 7 if top is not None
                else target_y - height
            )
        target_y = max(0, min(target_y, screen_height - height))
        self.window.geometry(f"+{target_x}+{target_y}")
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.deiconify()

    def _apply_setting(
        self, name: SettingKey, variable: tk.BooleanVar,
    ) -> None:
        self._actions.set_option(name, variable.get())

    @staticmethod
    def _button(
        parent: tk.Widget, title: str, command: Callable[[], None], *,
        side: Literal["left", "right", "top", "bottom"] = "top",
    ) -> tk.Button:
        button = tk.Button(
            parent, text=title, command=command, bg="#314158",
            fg="#edf5fe", activebackground="#506a89",
            activeforeground="#ffffff", relief="flat", bd=0,
            font=("Segoe UI", 9), padx=10, pady=5, cursor="hand2",
        )
        if side == "top":
            button.pack(fill="x", padx=8, pady=2)
        else:
            button.pack(side=side)
        return button

    def _invoke(self, command: Callable[[], None]) -> None:
        self.close()
        command()

    def _quit(self) -> None:
        self.close()
        self._actions.quit()

    def contains_pointer(self, px: int, py: int) -> bool:
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (
            x <= px < x + self.window.winfo_width()
            and y <= py < y + self.window.winfo_height()
        )

    def close(self) -> None:
        self.window.destroy()
        self._actions.closed()
