"""Settings popover for user-configurable desktop pet behaviour."""

from __future__ import annotations

import sys
import time
import tkinter as tk
from functools import partial
from typing import TYPE_CHECKING, Callable, Literal

if TYPE_CHECKING:
    from ..gui import DesktopPet

class SettingsPopup:
    """Explicitly controlled settings window; no fragile native menu grab."""

    def __init__(self, pet: DesktopPet, x: int, y: int) -> None:
        self.pet = pet
        self.window = tk.Toplevel(pet.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg="#1b2635")
        self.window.wm_attributes("-topmost", pet.settings.always_on_top)
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
        self._button(frame, "Status und Aktionen ...",
                     partial(self._invoke, pet.open_status))
        self._button(frame, "Größe: 2× (Pixel)" if pet.settings.scale == 1
                     else "Größe: 1× (klein)",
                     partial(self._invoke, pet.toggle_scale))
        options = (
            ("always_on_top", "Immer im Vordergrund", pet.set_topmost),
            ("auto_walk", "An der Taskleiste laufen", pet.set_auto_walk),
            ("auto_routine", "Automatischer Tagesrhythmus", pet.set_auto_routine),
            ("follow_cursor", "Maus beobachten", pet.set_follow_cursor),
            ("spontaneous_talk", "Von selbst sprechen", pet.set_spontaneous_talk),
            ("observe_computer", "Rechnerauslastung beobachten", pet.set_observe_computer),
            ("learn_rhythm", "Meinen Rhythmus kennenlernen", pet.set_learn_rhythm),
        )
        for setting, label, setter in options:
            state = tk.BooleanVar(value=getattr(pet.settings, setting))
            self.values[setting] = state
            check = tk.Checkbutton(
                frame, text=label, variable=state,
                command=partial(self._apply_setting, state, setter),
                bg="#233042", fg="#edf5fe", selectcolor="#314158",
                activebackground="#314158", activeforeground="#ffffff",
                anchor="w", padx=9, pady=4, font=("Segoe UI", 9),
                bd=0, highlightthickness=0,
            )
            check.pack(fill="x", padx=7)
        self._button(frame, "Gelerntes Tagesmuster löschen",
                     partial(self._invoke, pet.forget_rhythm))
        self._button(frame, "Leiste wieder neben Aiko",
                     partial(self._invoke, pet.reset_toolbar_position))
        self._button(frame, "Zur Taskleistenmitte", partial(self._invoke, pet.center))
        self._button(frame, "Beenden", self._quit)
        self.window.update_idletasks()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        screen_width = pet.root.winfo_screenwidth()
        screen_height = pet.root.winfo_screenheight()
        target_x = max(0, min(int(x - width), screen_width - width))
        target_y = int(y)
        if target_y + height + 8 > screen_height:
            target_y = (pet.toolbar.window.winfo_rooty() - height - 7
                        if pet.toolbar is not None else target_y - height)
        target_y = max(0, min(target_y, screen_height - height))
        self.window.geometry(f"+{target_x}+{target_y}")
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.deiconify()

    @staticmethod
    def _apply_setting(
        variable: tk.BooleanVar, setter: Callable[[bool], None],
    ) -> None:
        """Apply checkbox changes through their injected setting callback."""
        setter(variable.get())

    @staticmethod
    def _button(parent: tk.Widget, title: str,
                command: Callable[[], None],
                *, side: Literal["left", "right", "top", "bottom"] = "top") -> tk.Button:
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
        self.pet.quit()

    def contains_pointer(self, px: int, py: int) -> bool:
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return x <= px < x + self.window.winfo_width() and y <= py < y + self.window.winfo_height()

    def close(self) -> None:
        if self.pet.settings_popup is self:
            self.pet.settings_popup = None
            self.pet._menu_is_open = False
            self.pet._last_hover = time.monotonic()
        self.window.destroy()
