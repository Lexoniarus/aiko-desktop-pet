"""Status window for Aiko's needs, emotion and local computer activity."""

from __future__ import annotations

import tkinter as tk
from functools import partial
from typing import Callable

from .hover_contracts import HoverAnchor
from .status_contracts import StatusActions, StatusSnapshot

class StatusPanel:
    """Optional normal utility window (not part of the transparent hitbox)."""

    def __init__(
        self, root: tk.Tk, *, snapshot: Callable[[], StatusSnapshot],
        anchor: Callable[[], HoverAnchor], actions: StatusActions,
        always_on_top: bool,
    ) -> None:
        self.root = root
        self._snapshot = snapshot
        self._anchor = anchor
        self._actions = actions
        self.window = tk.Toplevel(root)
        self.window.title("Aiko · Status")
        self.window.resizable(False, False)
        self.window.configure(bg="#202733")
        self.window.attributes("-topmost", always_on_top)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.bind("<Control-q>", lambda _event: self._actions.quit())
        title = tk.Label(
            self.window, text="AIKO", font=("Segoe UI", 17, "bold"),
            fg="#b0e7fb", bg="#202733",
        )
        title.pack(padx=18, pady=(14, 2), anchor="w")
        self.today = tk.Label(
            self.window, text="", fg="#b0e7fb", bg="#202733",
            font=("Segoe UI", 10, "bold"), anchor="w", justify="left",
        )
        self.today.pack(padx=18, pady=(1, 0), anchor="w")
        self.next_event = tk.Label(
            self.window, text="", fg="#a7bacf", bg="#202733",
            font=("Segoe UI", 9), anchor="w", justify="left",
        )
        self.next_event.pack(padx=18, pady=(0, 9), anchor="w")
        self.hint = tk.Label(
            self.window, text="", fg="#cad4e0", bg="#202733",
            font=("Segoe UI", 9), anchor="w", justify="left", wraplength=235,
        )
        self.hint.pack(padx=18, pady=(0, 10), anchor="w")
        self.emotion_label = tk.Label(
            self.window, text="", fg="#b2cee0", bg="#202733",
            font=("Segoe UI", 9), anchor="w",
        )
        self.emotion_label.pack(padx=18, pady=(0, 6), anchor="w")
        self.hardware_label = tk.Label(
            self.window, text="", fg="#99b6c9", bg="#202733",
            font=("Segoe UI", 9), anchor="w", justify="left",
        )
        self.hardware_label.pack(padx=18, pady=(0, 5), anchor="w")
        self.life_label = tk.Label(
            self.window, text="", fg="#c4d7e7", bg="#202733",
            font=("Segoe UI", 9), anchor="w", justify="left",
            wraplength=248,
        )
        self.life_label.pack(padx=18, pady=(0, 10), anchor="w")
        self.bars: dict[str, tuple[tk.Canvas, int, tk.Label]] = {}
        for key, label, color in [
            ("satiety", "Sättigung", "#f5bd7a"),
            ("mood", "Laune", "#95ddc1"),
            ("energy", "Energie", "#98c9f5"),
            ("social", "Sozial", "#dda9ef"),
            ("affection", "Zuwendung", "#f0a5be"),
            ("friendship", "Freundschaft", "#ffb9c2"),
        ]:
            line = tk.Frame(self.window, bg="#202733")
            line.pack(fill="x", padx=18, pady=4)
            tk.Label(
                line, text=label, fg="#e9eef6", bg="#202733",
                width=10, anchor="w", font=("Segoe UI", 9),
            ).pack(side="left")
            bar = tk.Canvas(
                line, width=130, height=13, bg="#303b4a", bd=0,
                highlightthickness=0,
            )
            rect = bar.create_rectangle(0, 0, 1, 13, fill=color, outline="")
            bar.pack(side="left", padx=(0, 8))
            value = tk.Label(
                line, text="", fg="#e9eef6", bg="#202733",
                width=10, anchor="e", font=("Segoe UI", 9),
            )
            value.pack(side="left")
            self.bars[key] = (bar, rect, value)

        buttons = tk.Frame(self.window, bg="#202733")
        buttons.pack(padx=13, pady=(14, 10))
        for action, label in (
            ("feed", "Füttern"), ("play", "Spielen"), ("pet", "Streicheln"),
        ):
            tk.Button(
                buttons, text=label, command=partial(actions.interact, action),
                fg="#ffffff", bg="#39495e", activeforeground="#ffffff",
                activebackground="#51627a", relief="flat", padx=9, pady=5,
                font=("Segoe UI", 9),
            ).pack(side="left", padx=3)
        for action, label in (("talk", "Reden"), ("energy_drink", "Energy Drink +10")):
            tk.Button(
                buttons, text=label, command=partial(actions.interact, action),
                fg="#ffffff", bg="#39495e", activeforeground="#ffffff",
                activebackground="#51627a", relief="flat", padx=8, pady=5,
                font=("Segoe UI", 9),
            ).pack(side="left", padx=3)
        self.sleep_button = tk.Button(
            self.window, text="", command=partial(actions.interact, "sleep"),
            fg="#ffffff", bg="#344352", relief="flat", pady=5,
            activeforeground="#ffffff", activebackground="#536274",
            font=("Segoe UI", 9),
        )
        self.sleep_button.pack(fill="x", padx=18, pady=(0, 16))
        self.refresh()
        self.window.update_idletasks()
        x = max(0, min(
            root.winfo_screenwidth() - self.window.winfo_reqwidth(),
            root.winfo_x() - self.window.winfo_reqwidth() - 8,
        ))
        if x == 0:
            x = min(
                root.winfo_screenwidth() - self.window.winfo_reqwidth(),
                root.winfo_x() + self._anchor().width + 8,
            )
        y = max(0, min(
            root.winfo_screenheight() - self.window.winfo_reqheight() - 40,
            root.winfo_y(),
        ))
        self.window.geometry(f"+{x}+{y}")

    def refresh(self) -> None:
        """Render values from a detached status snapshot."""
        view = self._snapshot()
        self.today.configure(text=view.today)
        self.next_event.configure(text=view.next_event)
        self.hint.configure(text=view.hint)
        self.emotion_label.configure(text=view.emotion)
        self.sleep_button.configure(text=view.sleep_label)
        if self.hardware_label.cget("text") != view.hardware_line:
            self.hardware_label.configure(text=view.hardware_line)
        if self.life_label.cget("text") != view.activity_line:
            self.life_label.configure(text=view.activity_line)
        for name in self.bars:
            number = view.need_value(name)
            bar, rect, label = self.bars[name]
            bar.coords(rect, 0, 0, round(130 * number / 100), 13)
            value = f"{number:.0f}%"
            if name == "friendship":
                value += f" · Lv {view.friendship_level}"
            label.configure(text=value)

    def close(self) -> None:
        self.window.destroy()
        self._actions.closed()
