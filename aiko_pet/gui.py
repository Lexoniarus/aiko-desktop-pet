"""Frameless Windows desktop companion using only Tkinter and prepared PNGs.

Aiko lives along the Windows taskbar, follows the cursor with 16 hand-authored
gaze sprites and exposes her care actions in a mouse-hover toolbar.
"""

from __future__ import annotations

import math
import random
import sys
import time
import tkinter as tk
from dataclasses import replace
from tkinter import font as tkfont
from pathlib import Path
from tkinter import messagebox
from typing import Callable

from .adaptive import AdaptiveRoutine, Observation
from .config import load_env_file
from .desktop_input import GlobalMouseClicks, idle_seconds_windows
from .dialogue import AikoMind, ComputerVoice, EMOTION_LABELS, Reaction
from .gaze import gaze_sector
from .routine import TimeContext, context_at
from .reaction_sequence import Cue, EMOTES, compose_cues
from .storage import StateStore
from .system_activity import (
    ActivityMonitor, percent_label, workload_description, workload_intensity,
)
from .taskbar import TaskbarTrack, locate_primary_taskbar
from .window_stack import WindowStack

FRAME_WIDTH = 128
FRAME_HEIGHT = 208
TICK_MILLISECONDS = 140
MAGENTA = "#ff00ff"
ASSETS = Path(__file__).resolve().parent / "assets" / "frames"
EMOTE_ASSETS = Path(__file__).resolve().parent / "assets" / "emotes"
SCI_FI_UI = Path(__file__).resolve().parent / "assets" / "kenney_ui"
FRAME_COUNTS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
    "look": 16,
}
FRAME_TIMINGS = {
    "idle": 0.38,
    "running-left": 0.13,
    "running-right": 0.13,
    "waving": 0.22,
    "jumping": 0.18,
    "failed": 0.33,
    "waiting": 0.42,
    "running": 0.22,
    "review": 0.3,
}


class StatusPanel:
    """Optional normal utility window (not part of the transparent hitbox)."""

    def __init__(self, pet: DesktopPet) -> None:
        self.pet = pet
        self.window = tk.Toplevel(pet.root)
        self.window.title("Aiko · Status")
        self.window.resizable(False, False)
        self.window.configure(bg="#202733")
        self.window.attributes("-topmost", pet.settings.always_on_top)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.bind("<Escape>", lambda _event: self.close())
        self.window.bind("<Control-q>", lambda _event: pet.quit())
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
        for action, label in (("feed", "Füttern"), ("play", "Spielen"), ("pet", "Streicheln")):
            tk.Button(
                buttons, text=label, command=lambda a=action: pet.interact(a),
                fg="#ffffff", bg="#39495e", activeforeground="#ffffff",
                activebackground="#51627a", relief="flat", padx=9, pady=5,
                font=("Segoe UI", 9),
            ).pack(side="left", padx=3)
        for action, label in (("talk", "Reden"), ("energy_drink", "Energy Drink +10")):
            tk.Button(
                buttons, text=label, command=lambda a=action: pet.interact(a),
                fg="#ffffff", bg="#39495e", activeforeground="#ffffff",
                activebackground="#51627a", relief="flat", padx=8, pady=5,
                font=("Segoe UI", 9),
            ).pack(side="left", padx=3)
        self.sleep_button = tk.Button(
            self.window, text="", command=lambda: pet.interact("sleep"),
            fg="#ffffff", bg="#344352", relief="flat", pady=5,
            activeforeground="#ffffff", activebackground="#536274",
            font=("Segoe UI", 9),
        )
        self.sleep_button.pack(fill="x", padx=18, pady=(0, 16))
        self.refresh()
        self.window.update_idletasks()
        x = max(0, min(
            pet.root.winfo_screenwidth() - self.window.winfo_reqwidth(),
            pet.root.winfo_x() - self.window.winfo_reqwidth() - 8,
        ))
        if x == 0:
            x = min(
                pet.root.winfo_screenwidth() - self.window.winfo_reqwidth(),
                pet.root.winfo_x() + pet.width + 8,
            )
        y = max(0, min(
            pet.root.winfo_screenheight() - self.window.winfo_reqheight() - 40,
            pet.root.winfo_y(),
        ))
        self.window.geometry(f"+{x}+{y}")

    def refresh(self) -> None:
        state = self.pet.state
        context = self.pet.context
        self.today.configure(text=context.label)
        self.next_event.configure(text=context.schedule_line)
        self.hint.configure(text=state.mood_hint(context))
        emotion = self.pet.mind.emotion(state, time.monotonic())
        self.emotion_label.configure(text=f"Stimmung: {EMOTION_LABELS[emotion]}")
        self.sleep_button.configure(text="Wecken" if state.sleeping else "Schlafen")
        if self.pet.settings.observe_computer:
            snapshot = self.pet.activity_monitor.latest()
            line = (f"CPU {percent_label(snapshot.cpu)}  ·  "
                    f"GPU {percent_label(snapshot.gpu)}  ·  "
                    f"RAM {percent_label(snapshot.ram)}")
        else:
            line = "Rechnerbeobachtung deaktiviert"
        if self.hardware_label.cget("text") != line:
            self.hardware_label.configure(text=line)
        behaviour = self.pet.adaptive.current
        if self.pet.settings.observe_computer and behaviour is not None:
            labels = {
                "working": "Konzentriert bei der Arbeit",
                "recovering": "Nach der Arbeit zur Ruhe kommen",
                "resting": "Eine ruhige Pause genießen",
                "present": "Wach und aufmerksam",
                "wandering": "Zeit für mich",
            }
            description = labels.get(behaviour.mode, "Ich bin hier")
            if behaviour.expectation_confident:
                description += " · eingespielter Tagesrhythmus"
            line = (f"Mein Rhythmus: {description} · "
                    f"Beanspruchung {behaviour.strain:.0f}/100")
            if behaviour.uptime_hours is not None:
                line += f" · Rechnerlaufzeit {behaviour.uptime_hours:.1f} h"
        else:
            line = "Mein Rhythmus: lernt noch" if self.pet.settings.observe_computer else ""
        if self.life_label.cget("text") != line:
            self.life_label.configure(text=line)
        for name in self.bars:
            number = getattr(state, name)
            bar, rect, label = self.bars[name]
            bar.coords(rect, 0, 0, round(130 * number / 100), 13)
            label.configure(
                text=f"{number:.0f}%" +
                (f" · Lv {state.friendship_level}" if name == "friendship" else ""),
            )

    def close(self) -> None:
        self.window.destroy()
        self.pet.status_panel = None



class ActionToolbar:
    """Kenney sci-fi hover status; all six controls remain clickable."""

    NEEDS = (
        ("satiety", "Sättigung", "#f5bd7a"),
        ("mood", "Laune", "#95ddc1"),
        ("energy", "Energie", "#98c9f5"),
        ("social", "Sozial", "#dda9ef"),
        ("affection", "Zuwendung", "#f0a5be"),
        ("friendship", "Freundschaft", "#ffb9c2"),
    )
    BAR_WIDTH = 92
    BACKGROUND = "#D7DCE8"
    TEXT = "#414B5F"
    SUBTEXT = "#617189"

    def __init__(self, pet: DesktopPet) -> None:
        self.pet = pet
        self.window = tk.Toplevel(pet.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg="#8E9CB1")
        # Assets are pre-rendered with Kenney CC0 tiles. The optional user-
        # supplied Kenney Mini font is used only if installed on Windows;
        # font files are not packaged with Aiko.
        try:
            available_fonts = set(tkfont.families(root=pet.root))
        except tk.TclError:
            available_fonts = set()
        self.font_family = (
            "Kenney Mini" if "Kenney Mini" in available_fonts else "Segoe UI"
        )
        self._button_images = {
            key: tk.PhotoImage(file=str(SCI_FI_UI / f"button_{key}.png"))
            for key in ("regular", "wide", "small")
        }
        self._header_image = tk.PhotoImage(file=str(SCI_FI_UI / "toolbar_banner.png"))
        self.window.wm_attributes("-topmost", pet.settings.always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)

        outer = tk.Frame(
            self.window, bg=self.BACKGROUND, highlightthickness=2,
            highlightbackground="#E9ECF5", bd=0,
        )
        outer.pack(padx=3, pady=3)
        self.today = tk.Label(
            outer, text="", image=self._header_image, compound="center",
            font=(self.font_family, 10, "bold"),
            fg="#FFFFFF", bg="#2998D4", anchor="w", padx=14, pady=0,
        )
        self.today.pack(side="top", fill="x")
        # Drag by the title area, not by the care buttons.
        self._drag_origin: tuple[int, int, int, int] | None = None
        self._dragging = False
        self.today.configure(cursor="fleur")
        self.today.bind("<ButtonPress-1>", self._drag_start)
        self.today.bind("<B1-Motion>", self._drag_motion)
        self.today.bind("<ButtonRelease-1>", self._drag_end)

        # Two compact rows keep all six values visible on smaller desktops.
        needs_frame = tk.Frame(outer, bg=self.BACKGROUND)
        needs_frame.pack(fill="x", padx=7, pady=(1, 5))
        self.needs: dict[str, tuple[tk.Canvas, int, tk.Label]] = {}
        for column in range(3):
            needs_frame.columnconfigure(column, weight=1, uniform="needs")
        for i, (key, title, color) in enumerate(self.NEEDS):
            cell = tk.Frame(needs_frame, bg=self.BACKGROUND)
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=3, pady=2)
            label = tk.Label(
                cell, text="", font=(self.font_family, 9), width=20,
                fg=self.TEXT, bg=self.BACKGROUND, anchor="w",
            )
            label.pack(anchor="w")
            bar = tk.Canvas(
                cell, width=self.BAR_WIDTH, height=10, bd=0,
                highlightthickness=0, bg="#969FB2",
            )
            rect = bar.create_rectangle(0, 0, 1, 10, outline="", fill=color)
            bar.pack(fill="x", pady=(3, 3))
            self.needs[key] = (bar, rect, label)
            bar.bind(
                "<Configure>",
                lambda event, need=key: self._resize_need(need, event.width),
            )

        actions_frame = tk.Frame(outer, bg=self.BACKGROUND)
        actions_frame.pack(fill="x", padx=5)
        actions_row = tk.Frame(actions_frame, bg=self.BACKGROUND)
        actions_row.pack(fill="x")
        extra_row = tk.Frame(actions_frame, bg=self.BACKGROUND)
        extra_row.pack(fill="x")
        self.buttons: dict[str, tk.Button] = {}
        for action, title, parent in (
            ("feed", "Snack", actions_row),
            ("play", "Spielen", actions_row),
            ("pet", "Streicheln", actions_row),
            ("talk", "Reden", actions_row),
            ("energy_drink", "Energy Drink +10", extra_row),
            ("sleep", "Schlafen", extra_row),
        ):
            self.buttons[action] = self._button(
                parent, title, lambda selected=action: self.pet.interact(selected),
            )
        self._button(extra_row, "Status", pet.open_status)
        self.settings_button = self._button(extra_row, "⋯", self._open_settings)

        self.hardware = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.SUBTEXT, bg=self.BACKGROUND, anchor="w", padx=10, pady=3,
        )
        self.hardware.pack(fill="x")
        self.workload = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.TEXT, bg=self.BACKGROUND, anchor="w", padx=10, pady=3,
        )
        self.workload.pack(fill="x")
        self.visible = False
        self._last_placement: tuple[int, int, int, int] | None = None

    def _button(
        self, parent: tk.Widget, text: str, command: Callable[[], None],
    ) -> tk.Button:
        if text == "⋯":
            image = self._button_images["small"]
        elif len(text) > 13:
            image = self._button_images["wide"]
        else:
            image = self._button_images["regular"]
        button = tk.Button(
            parent, text=text, command=command,
            image=image, compound="center", font=(self.font_family, 9),
            fg="#344256", bg=self.BACKGROUND,
            activeforeground="#0B6DAA", activebackground=self.BACKGROUND,
            bd=0, relief="flat", padx=0, pady=0,
            highlightthickness=0, cursor="hand2",
        )
        button.pack(side="left", padx=2, pady=4)
        return button

    def _open_settings(self) -> None:
        # A normal Toplevel popover is predictable on Windows: native Tk menus
        # can fail to emit Unmap, leaving a permanent hover/menu lock.
        button = self.settings_button
        self.pet.toggle_settings_menu(
            button.winfo_rootx() + button.winfo_width(),
            button.winfo_rooty(),
        )

    def _resize_need(self, key: str, width: int | None = None) -> None:
        """Fill the *actual displayed* canvas, not its nominal requested width."""
        bar, rect, _label = self.needs[key]
        actual_width = width if width is not None else bar.winfo_width()
        if actual_width <= 1:
            actual_width = bar.winfo_reqwidth()
        amount = max(0.0, min(100.0, getattr(self.pet.state, key)))
        bar.coords(rect, 0, 0, round(actual_width * amount / 100), 10)

    def refresh(self) -> None:
        desired = "Wecken" if self.pet.state.sleeping else "Schlafen"
        feed_label = self.pet.state.feed_label(self.pet.context)
        changed = False
        for widget, value in (
            (self.buttons["sleep"], desired),
            (self.buttons["feed"], feed_label),
            (self.today, f"{self.pet.context.label}   ↔ Ziehen"),
        ):
            if widget.cget("text") != value:
                widget.configure(text=value)
                changed = True
        for key, title, _color in self.NEEDS:
            amount = max(0, min(100, getattr(self.pet.state, key)))
            _bar, _rect, label = self.needs[key]
            text = f"{title}  {amount:.0f}%"
            if key == "friendship":
                text = f"{title}  {amount:.0f}% · Lv {self.pet.state.friendship_level}"
            if label.cget("text") != text:
                label.configure(text=text)
            self._resize_need(key)
        reading = self.pet.activity_monitor.latest()
        if self.pet.settings.observe_computer:
            hardware_line = (
                f"MEIN RECHNER   CPU {percent_label(reading.cpu)}"
                f"   ·   GPU {percent_label(reading.gpu)}"
                f"   ·   RAM {percent_label(reading.ram)}"
            )
            work_line = workload_description(reading)
        else:
            hardware_line = "Rechnerbeobachtung deaktiviert"
            work_line = ""
        for widget, value in ((self.hardware, hardware_line),
                              (self.workload, work_line)):
            if widget.cget("text") != value:
                widget.configure(text=value)
                changed = True
        if changed and self.visible:
            self.place()

    def contains_pointer(self, px: int, py: int) -> bool:
        if not self.visible:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (x <= px < x + self.window.winfo_width()
                and y <= py < y + self.window.winfo_height())

    def contains_bridge(self, px: int, py: int) -> bool:
        """Tolerate the small horizontal or vertical gap to the sprite."""
        if not self.visible or self.pet.settings.toolbar_x is not None:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        width, height = self.window.winfo_width(), self.window.winfo_height()
        pet_x, pet_y = self.pet.root.winfo_rootx(), self.pet.root.winfo_rooty()
        pet_right = pet_x + self.pet.width
        bar_right = x + width
        top = max(y, pet_y)
        bottom = min(y + height, pet_y + self.pet.height)
        if top <= bottom:
            if bar_right <= pet_x:
                return bar_right - 3 <= px <= pet_x + 5 and top <= py <= bottom
            if pet_right <= x:
                return pet_right - 5 <= px <= x + 3 and top <= py <= bottom
        left = max(x, pet_x)
        right = min(bar_right, pet_right)
        if left <= right:
            return left <= px <= right and y + height - 3 <= py <= pet_y + 10
        return False

    def place(self) -> None:
        """Dragged panel stays put; default stays beside Aiko's head."""
        if self._dragging:
            return
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        screen_width = self.pet.root.winfo_screenwidth()
        screen_height = self.pet.root.winfo_screenheight()
        if self.pet.settings.toolbar_x is not None and self.pet.settings.toolbar_y is not None:
            x, y = self.pet.settings.toolbar_x, self.pet.settings.toolbar_y
        else:
            pet_x = self.pet.settings.x or 0
            pet_y = self.pet.settings.y or 0
            right_x = pet_x + self.pet.width + 10
            left_x = pet_x - width - 10
            x = right_x if right_x + width <= screen_width else left_x
            y = pet_y + max(0, (self.pet.height - height) // 2)
        x = max(0, min(round(x), max(0, screen_width - width)))
        y = max(0, min(round(y), max(0, screen_height - height)))
        placement = x, y, width, height
        if placement != self._last_placement:
            self.window.geometry(f"+{x}+{y}")
            self._last_placement = placement

    def _drag_start(self, event: tk.Event) -> None:
        self._dragging = True
        self._drag_origin = (
            event.x_root, event.y_root,
            self.window.winfo_rootx(), self.window.winfo_rooty(),
        )

    def _drag_motion(self, event: tk.Event) -> None:
        if self._drag_origin is None:
            return
        px, py, x, y = self._drag_origin
        width, height = self.window.winfo_width(), self.window.winfo_height()
        screen_w = self.pet.root.winfo_screenwidth()
        screen_h = self.pet.root.winfo_screenheight()
        new_x = max(0, min(x + event.x_root - px, max(0, screen_w - width)))
        new_y = max(0, min(y + event.y_root - py, max(0, screen_h - height)))
        self.window.geometry(f"+{new_x}+{new_y}")
        self._last_placement = (new_x, new_y, width, height)
        self.pet._move_bubble()

    def _drag_end(self, _event: tk.Event) -> None:
        if self._drag_origin is None:
            return
        # The window manager may not have acknowledged our last geometry
        # request before ButtonRelease; save the requested, clamped position.
        position = self._last_placement
        self.pet.settings.toolbar_x = position[0] if position is not None else self.window.winfo_rootx()
        self.pet.settings.toolbar_y = position[1] if position is not None else self.window.winfo_rooty()
        self._drag_origin = None
        self._dragging = False
        self.pet._last_hover = time.monotonic()
        self.pet._save()

    def reset_position(self) -> None:
        self.pet.settings.toolbar_x = None
        self.pet.settings.toolbar_y = None
        self._last_placement = None
        if self.visible:
            self.place()
        self.pet._save()

    def show(self) -> None:
        if self.visible:
            return
        self.refresh()
        self.place()
        self.window.deiconify()
        self.visible = True
        self.pet._move_bubble()
        self.pet._overlay_stack.restore()

    def hide(self) -> None:
        if not self.visible:
            return
        self.visible = False
        self.window.withdraw()
        # Window managers may discard pending movements during withdrawal.
        self._last_placement = None
        self.pet._move_bubble()

    def close(self) -> None:
        self.window.destroy()


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
                     lambda: self._invoke(pet.open_status))
        self._button(frame, "Größe: 2× (Pixel)" if pet.settings.scale == 1
                     else "Größe: 1× (klein)",
                     lambda: self._invoke(pet.toggle_scale))
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
                command=lambda variable=state, change=setter: change(variable.get()),
                bg="#233042", fg="#edf5fe", selectcolor="#314158",
                activebackground="#314158", activeforeground="#ffffff",
                anchor="w", padx=9, pady=4, font=("Segoe UI", 9),
                bd=0, highlightthickness=0,
            )
            check.pack(fill="x", padx=7)
        self._button(frame, "Gelerntes Tagesmuster löschen",
                     lambda: self._invoke(pet.forget_rhythm))
        self._button(frame, "Leiste wieder neben Aiko",
                     lambda: self._invoke(pet.reset_toolbar_position))
        self._button(frame, "Zur Taskleistenmitte", lambda: self._invoke(pet.center))
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
    def _button(parent: tk.Widget, title: str,
                command: Callable[[], None], *, side: str = "top") -> tk.Button:
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


class DesktopPet:
    def __init__(
        self, *, store: StateStore | None = None,
        activity_monitor: ActivityMonitor | None = None,
    ) -> None:
        self.store = store or StateStore()
        self.state, self.settings = self.store.load()
        self.adaptive = AdaptiveRoutine(self.store.load_memory())
        self.context: TimeContext = context_at(time.time())
        self.root = tk.Tk()
        self._speech_font = (
            "Kenney Mini" if "Kenney Mini" in set(tkfont.families(root=self.root))
            else "Segoe UI"
        )
        # A mapped Tk root briefly appears at (0, 0) before its first geometry.
        # Keep it invisible until the real taskbar coordinates are applied.
        self.root.withdraw()
        self._placed = False
        self.root.title("Aiko Desktop Pet")
        self.root.overrideredirect(True)
        self.root.configure(bg=MAGENTA if sys.platform == "win32" else "#202733")
        if sys.platform == "win32":
            # Windows colorkey: transparent margins around the PNGs are not a box.
            self.root.wm_attributes("-transparentcolor", MAGENTA)
        self.root.wm_attributes("-topmost", self.settings.always_on_top)
        self.background = MAGENTA if sys.platform == "win32" else "#202733"
        self.width = FRAME_WIDTH * self.settings.scale
        self.height = FRAME_HEIGHT * self.settings.scale
        self.canvas = tk.Canvas(
            self.root, width=self.width, height=self.height,
            bg=self.background, borderwidth=0, highlightthickness=0,
        )
        self.canvas.pack()
        self.sprites = self._load_sprites()
        self.image_item = self.canvas.create_image(
            0, 0, anchor="nw", image=self.sprites["idle"][0],
        )
        self._last_sprite_key: tuple[str, int | None] | None = None
        self._frame_index = 0
        self._frame_started = time.monotonic()
        self._last_tick = time.monotonic()
        self._last_track_check = self._last_tick
        self._action_until = 0.0
        self._action_state = "idle"
        self._walk_remaining = 0.0
        self._next_walk = time.monotonic() + random.uniform(3.0, 8.0)
        self._last_saved = time.monotonic()
        self.mind = AikoMind(started_at=self._last_saved)
        self.computer_voice = ComputerVoice()
        self.activity_monitor = activity_monitor or ActivityMonitor()
        self.activity_monitor.set_enabled(self.settings.observe_computer)
        self._menu_is_open = False
        self.settings_popup: SettingsPopup | None = None
        self._mouse_clicks = GlobalMouseClicks()
        self._mouse_clicks.clicked()  # establish a baseline before showing UI
        self._last_hardware_sample = 0.0
        self._last_adaptive_sample = 0.0
        self._pending_computer_line: tuple[str, float] | None = None
        self._closed = False
        self._scheduled_tick: str | None = None
        self._scheduled_greeting: str | None = None
        self._last_spoken = -1000.0
        self._next_comment = self._last_saved + random.uniform(180.0, 360.0)
        self._next_cursor_line = self._last_saved + random.uniform(200.0, 420.0)
        self._next_idle_emote = self._last_saved + random.uniform(70.0, 170.0)
        self._last_hover = -100.0
        self._gaze_sector: int | None = None
        self._previous_pointer: tuple[int, int] | None = None
        self._last_pointer_move = -100.0
        self._last_attention = -100.0
        self._attention_until = -100.0
        self._bubble: tk.Toplevel | None = None
        self._bubble_timeout: str | None = None
        self._followup_timeout: str | None = None
        self._speech_generation = 0
        self._reaction_cues: tuple[Cue, ...] = ()
        self._emote_images: dict[str, tk.PhotoImage] = {}
        self.toolbar: ActionToolbar | None = None
        self.status_panel: StatusPanel | None = None
        self._overlay_stack = WindowStack(
            self._overlay_windows, enabled=self.settings.always_on_top,
        )
        self._last_stack_check = self._last_tick
        self.track: TaskbarTrack = locate_primary_taskbar(
            self.root.winfo_screenwidth(), self.root.winfo_screenheight(),
        )
        self._setup_events()
        self._place_initially()
        self.root.update_idletasks()
        self.root.deiconify()
        self._overlay_stack.restore()
        self.activity_monitor.start()
        self._scheduled_greeting = self.root.after(460, self._greet_on_start)
        self._scheduled_tick = self.root.after(TICK_MILLISECONDS, self._tick)

    def _overlay_windows(self) -> list[tk.Tk | tk.Toplevel]:
        """Back-to-front display order, independent of Tk's focus state."""
        windows: list[tk.Tk | tk.Toplevel] = [self.root]
        if self.toolbar is not None and self.toolbar.visible:
            windows.append(self.toolbar.window)
        if self.status_panel is not None:
            windows.append(self.status_panel.window)
        if self._bubble is not None:
            windows.append(self._bubble)
        if self.settings_popup is not None:
            windows.append(self.settings_popup.window)
        return windows

    def _load_sprites(self) -> dict[str, list[tk.PhotoImage]]:
        sprites: dict[str, list[tk.PhotoImage]] = {}
        for state, count in FRAME_COUNTS.items():
            frames: list[tk.PhotoImage] = []
            for i in range(count):
                path = ASSETS / state / f"{i:02d}.png"
                if not path.is_file():
                    raise FileNotFoundError(f"Missing sprite: {path}")
                frame = tk.PhotoImage(file=str(path))
                if (frame.width(), frame.height()) != (FRAME_WIDTH, FRAME_HEIGHT):
                    raise ValueError(f"Invalid sprite dimensions: {path}")
                if self.settings.scale == 2:
                    frame = frame.zoom(2, 2)
                frames.append(frame)
            sprites[state] = frames
        return sprites

    def _setup_events(self) -> None:
        # The care controls stay in the hover bar, but mouse clicks now
        # get their own expressive reactions. Shift+right-click opens settings.
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Button-1>", self._on_click_left)
        self.canvas.bind("<Button-3>", self._on_click_right)
        self.canvas.bind("<Shift-Button-3>", self._show_menu)
        self.root.bind("<Control-q>", lambda _event: self.quit())
        self.root.bind("<F2>", lambda _event: self.open_status())
        self.root.bind_all("<ButtonPress>", self._on_tk_press, add="+")
        self.root.bind_all("<FocusOut>", self._on_focus_out, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def _place_initially(self) -> None:
        if self.settings.x is None:
            x = self.track.left + round((self.track.right - self.track.left) * 0.75)
        else:
            x = self.settings.x  # Older save data: keep x, ignore obsolete y.
        self._place_x(x)

    def _place_x(self, x: float) -> None:
        new_x = self.track.clamp_x(x, self.width)
        new_y = self.track.sprite_y(self.settings.scale)
        if (new_x, new_y) == (self.settings.x, self.settings.y) and self._placed:
            return
        self.settings.x = new_x
        self.settings.y = new_y
        self.root.geometry(f"{self.width}x{self.height}+{new_x}+{new_y}")
        self._placed = True
        if self.toolbar is not None and self.toolbar.visible:
            self.toolbar.place()
        self._move_bubble()

    def _on_enter(self, _event: tk.Event | None = None) -> None:
        now = time.monotonic()
        # Only the first Enter after a long absence gets a welcome back;
        # repeatedly refreshing hover must not spam the same response.
        was_hidden = self.toolbar is None or not self.toolbar.visible
        reaction = (
            self.mind.return_to_pet(self.state, self.context, now)
            if was_hidden else None
        )
        self._last_hover = now
        self._walk_remaining = 0
        self._next_walk = now + random.uniform(3.0, 6.0)
        if self.toolbar is None:
            self.toolbar = ActionToolbar(self)
        self.toolbar.show()
        self._react(reaction, 2800)

    def _on_click_left(self, _event: tk.Event | None = None) -> None:
        self._on_enter()
        now = time.monotonic()
        self.adaptive.note_interaction(time.time())
        self._react_to_click(self.mind.click("left", self.state, self.context, now))

    def _on_click_right(self, _event: tk.Event | None = None) -> None:
        self._on_enter()
        now = time.monotonic()
        self.adaptive.note_interaction(time.time())
        self._react_to_click(self.mind.click("right", self.state, self.context, now))

    def _greet_on_start(self) -> None:
        # A startup hello must never interrupt an immediate user interaction.
        if (not self.settings.spontaneous_talk or
                time.monotonic() - self._last_spoken < 15):
            return
        self._react(
            self.mind.say_event(
                "greeting", self.state, self.context, time.monotonic(),
            ), 3300,
        )

    def _cancel_followup(self) -> None:
        if self._followup_timeout is not None:
            self.root.after_cancel(self._followup_timeout)
            self._followup_timeout = None
        self._speech_generation += 1
        self._reaction_cues = ()

    def _react_to_click(self, reaction: Reaction | None) -> None:
        if reaction is None:
            # Deliberate silence must not be followed by a stale second line.
            self._cancel_followup()
            self._hide_bubble()
            return
        # During rapid tapping, skip the opening icon so the actual response
        # remains visible instead of resetting the same 700ms cue forever.
        if len(self.mind.clicks) >= 3 and reaction.emote_before is not None:
            reaction = replace(reaction, emote_before=None)
        self._react(reaction, 2800)

    def _react(self, reaction: Reaction | None, duration_ms: int = 2600) -> None:
        if reaction is None:
            return
        self._cancel_followup()
        generation = self._speech_generation
        if not self.state.sleeping and reaction.animation != "idle":
            self._start_action(reaction.animation, min(2.0, duration_ms / 1600))
        self._last_spoken = time.monotonic()
        if reaction.emote_before is not None or reaction.emote_after is not None:
            self._reaction_cues = compose_cues(
                reaction.text, before=reaction.emote_before,
                followup=reaction.followup_text,
                after=reaction.emote_after,
                minimum_text_ms=max(1700, duration_ms - 500),
            )
            self._advance_reaction(generation, 0)
            return
        # Backward-compatible plain speech and self-correction sequences.
        self.say(reaction.text, max(duration_ms, reaction.followup_delay_ms + 200))
        if reaction.followup_text:
            self._followup_timeout = self.root.after(
                reaction.followup_delay_ms,
                lambda: self._show_followup(generation, reaction.followup_text),
            )

    def _advance_reaction(self, generation: int, index: int) -> None:
        """Replace the previous visual beat; no emote/text overlap."""
        self._followup_timeout = None
        if self._closed or generation != self._speech_generation:
            return
        if index >= len(self._reaction_cues):
            self._reaction_cues = ()
            return
        cue = self._reaction_cues[index]
        if cue.kind == "emote":
            self._show_emote(cue.content, cue.duration_ms)
        else:
            self.say(cue.content, cue.duration_ms)
        self._last_spoken = time.monotonic()
        if index + 1 < len(self._reaction_cues):
            self._followup_timeout = self.root.after(
                cue.duration_ms,
                lambda: self._advance_reaction(generation, index + 1),
            )
        else:
            self._followup_timeout = self.root.after(
                cue.duration_ms, lambda: self._complete_reaction(generation),
            )

    def _complete_reaction(self, generation: int) -> None:
        self._followup_timeout = None
        if generation == self._speech_generation:
            self._reaction_cues = ()

    def _show_followup(self, generation: int, text: str) -> None:
        self._followup_timeout = None
        if self._closed or generation != self._speech_generation:
            return
        self.say(text, 2600)
        self._last_spoken = time.monotonic()

    def _pointer_in_pet_or_toolbar(self, px: int, py: int) -> bool:
        under = self.root.winfo_containing(px, py)
        over_pet = under is self.root or under is self.canvas
        over_toolbar = (
            self.toolbar is not None and
            (self.toolbar.contains_pointer(px, py)
             or self.toolbar.contains_bridge(px, py))
        )
        return bool(over_pet or over_toolbar)

    def _dismiss_if_outside(self, px: int, py: int) -> None:
        """One click anywhere else closes temporary controls immediately."""
        if self.toolbar is not None and self.toolbar._dragging:
            return
        over_ui = self._pointer_in_pet_or_toolbar(px, py)
        over_popup = (
            self.settings_popup is not None
            and self.settings_popup.contains_pointer(px, py)
        )
        if self.settings_popup is not None and not over_popup and not over_ui:
            self.settings_popup.close()
        if self.toolbar is not None and self.toolbar.visible and not (over_ui or over_popup):
            self.toolbar.hide()

    def _on_tk_press(self, event: tk.Event) -> None:
        # Tk covers clicks inside Aiko's own windows; the Windows mouse-state
        # poll below also catches clicks in other applications.
        self._dismiss_if_outside(event.x_root, event.y_root)

    def _on_focus_out(self, _event: tk.Event) -> None:
        # Fallback for focus changes Tk receives while another app is clicked.
        if not self._closed:
            self.root.after(100, self._dismiss_after_focus_loss)

    def _dismiss_after_focus_loss(self) -> None:
        if self._closed:
            return
        self._dismiss_if_outside(
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
        )

    def _refresh_hover(self, now: float) -> None:
        if self.toolbar is not None and self.toolbar._dragging:
            self._last_hover = now
            return
        if self.settings_popup is not None:
            return  # User is actively using her settings popover.
        px, py = self.root.winfo_pointerx(), self.root.winfo_pointery()
        if self._pointer_in_pet_or_toolbar(px, py):
            self._last_hover = now
            under = self.root.winfo_containing(px, py)
            if under in (self.root, self.canvas) and (
                self.toolbar is None or not self.toolbar.visible
            ):
                self._on_enter()
            self.mind.last_contact = now
        elif (
            self.toolbar is not None and self.toolbar.visible
            and now - self._last_hover >= (2.0 if self.settings.toolbar_x is not None else 0.9)
        ):
            self.toolbar.hide()

    def _show_menu(self, event: tk.Event) -> None:
        self.toggle_settings_menu(event.x_root, event.y_root)

    def toggle_settings_menu(self, x: int, y: int) -> None:
        if self.settings_popup is not None:
            self.settings_popup.close()
            return
        self._on_enter()
        self.settings_popup = SettingsPopup(self, x, y)
        self._menu_is_open = True
        self._overlay_stack.restore()

    def _poll_desktop_click(self) -> None:
        if self._mouse_clicks.clicked():
            self._dismiss_if_outside(
                self.root.winfo_pointerx(), self.root.winfo_pointery(),
            )

    def _start_action(
        self, state: str, duration: float, *, started_at: float | None = None,
    ) -> None:
        now = time.monotonic() if started_at is None else started_at
        self._action_state = state
        self._action_until = now + duration
        self._walk_remaining = 0
        self._next_walk = now + duration + random.uniform(2.5, 5)

    def interact(self, action: str) -> None:
        stamp = time.time()
        now = time.monotonic()
        self.state.advance(
            stamp, auto_routine=self.settings.auto_routine,
            allow_bedtime=self._allow_bedtime(),
            allow_nap=self._allow_nap(),
            interrupt_nap=self._interrupt_nap(),
            effort=self._live_effort(),
        )
        self.adaptive.note_interaction(stamp)
        self.context = context_at(stamp)
        event, previous_emotion = self.mind.care_event(
            action, self.state, self.context, now,
        )
        fallback = self.state.interact(action, now=stamp)
        if event not in ("play_tired", "energy_drink_full"):
            self.mind.after_care(action, now)
        response = self.mind.say_event(
            event, self.state, self.context, now, tone=previous_emotion,
        )
        if response is None:
            # A fallback must not be overwritten by an older, queued aside.
            self._cancel_followup()
            self.say(fallback, 2450)
        else:
            self._react(response, 2900)
        if self.toolbar is not None:
            self.toolbar.refresh()
        self._refresh_status()
        self._save()

    def set_topmost(self, value: bool) -> None:
        self.settings.always_on_top = bool(value)
        self._overlay_stack.enabled = self.settings.always_on_top
        self.root.wm_attributes("-topmost", self.settings.always_on_top)
        if self.toolbar is not None:
            self.toolbar.window.wm_attributes("-topmost", self.settings.always_on_top)
        if self.status_panel is not None:
            self.status_panel.window.wm_attributes("-topmost", self.settings.always_on_top)
        if self._bubble is not None:
            self._bubble.wm_attributes("-topmost", self.settings.always_on_top)
        if self.settings_popup is not None:
            self.settings_popup.window.wm_attributes(
                "-topmost", self.settings.always_on_top,
            )
        self._overlay_stack.restore()
        self._save()

    def set_auto_walk(self, value: bool) -> None:
        self.settings.auto_walk = bool(value)
        self._walk_remaining = 0
        self._next_walk = time.monotonic() + random.uniform(2.5, 5)
        self._save()

    def set_auto_routine(self, enabled: bool) -> None:
        self.settings.auto_routine = bool(enabled)
        self.state.advance(time.time(), auto_routine=self.settings.auto_routine)
        self.context = context_at(time.time())
        if self.toolbar is not None:
            self.toolbar.refresh()
        self._refresh_status()
        self._save()

    def set_follow_cursor(self, enabled: bool) -> None:
        self.settings.follow_cursor = bool(enabled)
        self._gaze_sector = None
        self._save()

    def set_spontaneous_talk(self, enabled: bool) -> None:
        self.settings.spontaneous_talk = bool(enabled)
        self._next_comment = time.monotonic() + random.uniform(180, 360)
        self._save()

    def set_learn_rhythm(self, enabled: bool) -> None:
        self.settings.learn_rhythm = bool(enabled)
        self._save()

    def forget_rhythm(self) -> None:
        self.adaptive.forget_profile()
        self._refresh_status()
        self._save()

    def set_observe_computer(self, enabled: bool) -> None:
        self.settings.observe_computer = bool(enabled)
        self.activity_monitor.set_enabled(self.settings.observe_computer)
        self.computer_voice.reset_samples()
        self._last_hardware_sample = 0.0
        self._last_adaptive_sample = 0.0
        self._pending_computer_line = None
        if not enabled:
            self.mind.set_situation(None)
        if self.toolbar is not None:
            self.toolbar.refresh()
        self._save()

    def toggle_scale(self) -> None:
        original_center = (self.settings.x or 0) + self.width / 2
        self.settings.scale = 2 if self.settings.scale == 1 else 1
        self.width = FRAME_WIDTH * self.settings.scale
        self.height = FRAME_HEIGHT * self.settings.scale
        self.sprites = self._load_sprites()
        self.canvas.config(width=self.width, height=self.height)
        self.canvas.itemconfigure(self.image_item, image=self.sprites["idle"][0])
        self._last_sprite_key = None
        self._gaze_sector = None
        self._placed = False  # Force Tk geometry update even at unchanged x/y.
        self._place_x(original_center - self.width / 2)
        if self.toolbar is not None and self.toolbar.visible:
            self.toolbar.place()
        self._save()

    def reset_toolbar_position(self) -> None:
        if self.toolbar is not None:
            self.toolbar.reset_position()
        else:
            self.settings.toolbar_x = None
            self.settings.toolbar_y = None
            self._save()

    def center(self) -> None:
        self._place_x((self.track.left + self.track.right - self.width) / 2)
        self._walk_remaining = 0
        self._save()

    def open_status(self) -> None:
        if self.status_panel is not None:
            self._overlay_stack.restore()
            return
        self.status_panel = StatusPanel(self)
        self._overlay_stack.restore()

    def _refresh_status(self) -> None:
        if self.status_panel is not None:
            self.status_panel.refresh()

    def _move_bubble(self) -> None:
        if self._bubble is None:
            return
        self._bubble.update_idletasks()
        width, height = self._bubble.winfo_reqwidth(), self._bubble.winfo_reqheight()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pet_x = self.settings.x or 0
        pet_y = self.settings.y or 0
        # The speech bubble belongs to Aiko, never to the status/hover bar.
        x = pet_x + (self.width - width) // 2
        y = pet_y - height - 7
        if y < 0:  # Taskbar at top: speak beside her head instead.
            y = pet_y + 4
            x = pet_x + self.width + 5
            if x + width > screen_w:
                x = pet_x - width - 5
        x = max(0, min(x, max(0, screen_w - width)))
        y = max(0, min(y, max(0, screen_h - height)))
        self._bubble.geometry(f"+{x}+{y}")
        # Moving a speech bubble must never lift it independently of Aiko.

    def _show_emote(self, emote: str, duration_ms: int = 900) -> None:
        """A single pixel emote, in exactly the same slot as speech bubbles."""
        if emote not in EMOTES:
            raise ValueError(f"Unsupported emote: {emote}")
        self._hide_bubble()
        bubble = tk.Toplevel(self.root)
        bubble.withdraw()
        bubble.overrideredirect(True)
        transparent = MAGENTA if sys.platform == "win32" else "#202733"
        bubble.configure(bg=transparent)
        bubble.wm_attributes("-topmost", self.settings.always_on_top)
        if sys.platform == "win32":
            bubble.wm_attributes("-toolwindow", True)
            bubble.wm_attributes("-transparentcolor", MAGENTA)
        if emote not in self._emote_images:
            path = EMOTE_ASSETS / f"emote_{emote}.png"
            if not path.is_file():
                bubble.destroy()
                raise FileNotFoundError(f"Missing emote: {path}")
            original = tk.PhotoImage(file=str(path))
            self._emote_images[emote] = original.zoom(3, 3)
        tk.Label(
            bubble, image=self._emote_images[emote],
            bg=transparent, borderwidth=0, highlightthickness=0,
        ).pack()
        self._bubble = bubble
        self._move_bubble()
        bubble.deiconify()
        self._overlay_stack.restore()
        self._bubble_timeout = self.root.after(duration_ms, self._hide_bubble)

    def _idle_emote(self) -> None:
        """Occasional unspoken state, never interrupting an existing scene."""
        if self._bubble is not None or self._followup_timeout is not None:
            return
        if self.state.energy < 20:
            emote = "sleeps"
        elif self.state.satiety < 18:
            emote = "drops"
        elif self.state.mood < 18:
            emote = "faceSad"
        elif self.state.affection < 18:
            emote = "heart"
        elif self.state.mood > 88:
            emote = "star"
        else:
            emote = "idea"
        self._show_emote(emote, 1100)

    def say(self, phrase: str, duration_ms: int = 1800) -> None:
        self._hide_bubble()
        bubble = tk.Toplevel(self.root)
        bubble.withdraw()
        bubble.overrideredirect(True)
        transparent = MAGENTA if sys.platform == "win32" else "#202733"
        bubble.configure(bg=transparent)
        bubble.wm_attributes("-topmost", self.settings.always_on_top)
        if sys.platform == "win32":
            bubble.wm_attributes("-toolwindow", True)
            bubble.wm_attributes("-transparentcolor", MAGENTA)
        frame = tk.Frame(bubble, bg="#53687e", bd=0)
        frame.pack()
        tk.Label(
            frame, text=phrase, font=(self._speech_font, 9), wraplength=235,
            bg="#f0f6fa", fg="#243247", justify="center",
            padx=12, pady=8,
        ).pack(padx=1, pady=1)
        # Two-color, pixel-style speech bubble tail; visible even for short text.
        tail = tk.Canvas(
            bubble, width=20, height=11, bg=transparent,
            highlightthickness=0, borderwidth=0,
        )
        tail.pack()
        tail.create_polygon(
            2, 0, 18, 0, 10, 10, fill="#f0f6fa",
            outline="#53687e", width=1,
        )
        self._bubble = bubble
        self._move_bubble()
        bubble.deiconify()
        self._overlay_stack.restore()
        self._bubble_timeout = self.root.after(duration_ms, self._hide_bubble)

    def _hide_bubble(self) -> None:
        if self._bubble_timeout is not None:
            self.root.after_cancel(self._bubble_timeout)
            self._bubble_timeout = None
        if self._bubble is not None:
            self._bubble.destroy()
            self._bubble = None

    def _gaze_direction(self, pointer: tuple[int, int]) -> int | None:
        if not self.settings.follow_cursor:
            self._gaze_sector = None
            return None
        eyes_x = self.root.winfo_x() + 63 * self.settings.scale
        eyes_y = self.root.winfo_y() + 82 * self.settings.scale
        # Tk pointer coordinates are absolute screen coordinates, even when
        # hovering another application's window or a second monitor.
        self._gaze_sector = gaze_sector(
            eyes_x, eyes_y, *pointer,
            scale=self.settings.scale, previous=self._gaze_sector,
        )
        return self._gaze_sector

    def _observe_pointer(self, now: float) -> tuple[int, int]:
        pointer = (self.root.winfo_pointerx(), self.root.winfo_pointery())
        moved = self._previous_pointer is not None and pointer != self._previous_pointer
        if moved:
            self._last_pointer_move = now
            # A short curious glance must not stop walking indefinitely.
            if now - self._last_attention >= 6.0:
                self._last_attention = now
                self._attention_until = now + 1.0
            if (
                self.settings.spontaneous_talk
                and self.settings.follow_cursor
                and now >= self._next_cursor_line
                and now - self._last_spoken > 100
                and not self.state.sleeping
                and (self.toolbar is None or not self.toolbar.visible)
                and random.random() < 0.08
            ):
                eye_x = (self.settings.x or 0) + 63 * self.settings.scale
                eye_y = (self.settings.y or 0) + 82 * self.settings.scale
                distance = math.hypot(pointer[0] - eye_x, pointer[1] - eye_y)
                event = (
                    "cursor_far" if distance > self.root.winfo_screenwidth() * 0.6
                    else "cursor_follow"
                )
                self._react(self.mind.say_event(event, self.state, self.context, now))
                self._next_cursor_line = now + random.uniform(280, 590)
        self._previous_pointer = pointer
        return pointer

    def _maybe_walk(self, now: float, dt: float) -> str | None:
        observed = self.adaptive.current
        busy = (observed.focused if observed is not None
                else self.activity_monitor.latest().is_busy())
        if self.settings.observe_computer and busy:
            # While Aiko is doing computer work, she concentrates in place.
            # Keeping review/idle animations costs no new artwork.
            self._walk_remaining = 0
            self._next_walk = max(self._next_walk, now + 2)
            return None
        if (
            not self.settings.auto_walk
            or self.state.sleeping
            or now < self._attention_until
            or (self.toolbar is not None and self.toolbar.visible)
        ):
            self._walk_remaining = 0
            return None
        if self._walk_remaining == 0 and now >= self._next_walk:
            slower = bool(observed is not None and observed.quiet)
            self._next_walk = now + (random.uniform(12, 24) if slower
                                    else random.uniform(4, 9))
            if self.state.energy >= 20:
                x = self.settings.x or 0
                limit = self.track.right - self.width
                if x <= self.track.left + 80:
                    direction = 1
                elif x >= limit - 80:
                    direction = -1
                else:
                    direction = random.choice((-1, 1))
                self._walk_remaining = direction * random.randint(100, 320)
        if self._walk_remaining == 0:
            return None
        direction = 1 if self._walk_remaining > 0 else -1
        pixels = direction * min(abs(self._walk_remaining), max(1.0, 64 * dt))
        old_x = self.settings.x or 0
        self._place_x(old_x + pixels)
        moved = (self.settings.x or 0) - old_x
        self._walk_remaining -= moved
        if moved == 0 or abs(self._walk_remaining) < 1:
            self._walk_remaining = 0
            if (
                self.settings.spontaneous_talk
                and now - self._last_spoken > 130
                and random.random() < 0.23
            ):
                self._react(self.mind.say_event(
                    "walk_pause", self.state, self.context, now,
                ))
        return "running-right" if direction > 0 else "running-left"

    def _show_frame(self, state: str, now: float, *, fixed: int | None = None) -> None:
        key = (state, fixed)
        if key != self._last_sprite_key:
            self._last_sprite_key = key
            self._frame_index = 0
            self._frame_started = now
        elif fixed is None and now - self._frame_started >= FRAME_TIMINGS.get(state, 0.3):
            self._frame_index = (self._frame_index + 1) % len(self.sprites[state])
            self._frame_started = now
        image = self.sprites[state][fixed if fixed is not None else self._frame_index]
        self.canvas.itemconfigure(self.image_item, image=image)

    def _react_to_computer(self, now: float) -> None:
        """React to new load measurements in seconds, without interrupting care."""
        if not self.settings.observe_computer:
            self._pending_computer_line = None
            return
        snapshot = self.activity_monitor.latest()
        if snapshot.measured_at > self._last_hardware_sample:
            self._last_hardware_sample = snapshot.measured_at
            event = self.computer_voice.observe_change(snapshot, now)
            if event and self.settings.spontaneous_talk and not self.state.sleeping:
                self._pending_computer_line = (event, now)
                if now >= self._action_until:
                    self._start_action("review", 1.4, started_at=now)
        if self._pending_computer_line is None:
            return
        event, observed_at = self._pending_computer_line
        if now - observed_at > 25 or not self.settings.spontaneous_talk or self.state.sleeping:
            self._pending_computer_line = None
        elif now >= self._action_until and now - self._last_spoken >= 7:
            response = self.mind.computer_event(
                event, self.state, self.context, now,
            )
            self._pending_computer_line = None
            if response is not None:
                self._react(response, 3400)
                self.computer_voice.last_voice_at = now

    def _interrupt_nap(self) -> bool:
        behaviour = self.adaptive.current
        return bool(self.settings.observe_computer and behaviour is not None
                    and behaviour.should_wake)

    def _allow_nap(self) -> bool:
        behaviour = self.adaptive.current
        return bool(self.settings.observe_computer and behaviour is not None
                    and behaviour.can_nap)

    def _allow_bedtime(self) -> bool | None:
        if not self.settings.observe_computer or self.adaptive.current is None:
            return None  # Keep the compatible v0.8 fallback.
        return self.adaptive.current.can_sleep

    def _live_effort(self) -> float | None:
        """Fresh local telemetry only. Never charge Aiko for unseen work."""
        if not self.settings.observe_computer:
            return None
        sample = self.activity_monitor.latest()
        age = time.monotonic() - sample.measured_at
        if not 0 <= age <= 18:
            return None
        return workload_intensity(sample)

    def _observe_adaptive(self, now: float, stamp: float) -> None:
        if not self.settings.observe_computer:
            return
        snapshot = self.activity_monitor.latest()
        if snapshot.measured_at <= self._last_adaptive_sample:
            return
        if snapshot.measured_at <= 0 or now - snapshot.measured_at > 25:
            return
        self._last_adaptive_sample = snapshot.measured_at
        observed = self.adaptive.observe(
            Observation(
                wall_time=stamp,
                effort=workload_intensity(snapshot),
                idle_seconds=idle_seconds_windows(),
                uptime_hours=snapshot.uptime_hours,
            ),
            now, energy=self.state.energy, sleeping=self.state.sleeping,
            manual_sleep=self.state.sleep_origin == "manual",
            learn=self.settings.learn_rhythm,
        )
        self.mind.set_situation(observed, now=now)

    def _tick(self) -> None:
        if self._closed:
            return
        # Tests and future manual refresh calls must not accumulate another
        # pending animation timer alongside the regularly scheduled one.
        if self._scheduled_tick is not None:
            self.root.after_cancel(self._scheduled_tick)
            self._scheduled_tick = None
        now = time.monotonic()
        dt = max(0.0, min(0.5, now - self._last_tick))
        self._last_tick = now
        stamp = time.time()
        was_sleeping = self.state.sleeping
        previous_period = (self.context.day_key, self.context.period)
        self._observe_adaptive(now, stamp)
        self.state.advance(
            stamp, auto_routine=self.settings.auto_routine,
            allow_bedtime=self._allow_bedtime(),
            allow_nap=self._allow_nap(),
            interrupt_nap=self._interrupt_nap(),
            effort=self._live_effort(),
        )
        self.context = context_at(stamp)
        current_period = (self.context.day_key, self.context.period)
        if current_period != previous_period:
            if self.toolbar is not None:
                self.toolbar.refresh()
            if self.settings.spontaneous_talk and self.state.sleeping != was_sleeping:
                event = "sleep" if self.state.sleeping else "wake"
                self._react(self.mind.say_event(event, self.state, self.context, now))
        if now - self._last_track_check >= 4.0:
            self._last_track_check = now
            new_track = locate_primary_taskbar(
                self.root.winfo_screenwidth(), self.root.winfo_screenheight(),
            )
            if new_track != self.track:
                self.track = new_track
                self._place_x(self.settings.x or self.track.left)
        self._poll_desktop_click()
        self._refresh_hover(now)
        self._react_to_computer(now)
        pointer = self._observe_pointer(now)
        if self.state.sleeping:
            self._walk_remaining = 0
            self._show_frame("idle", now, fixed=2)
        elif now < self._action_until:
            self._show_frame(self._action_state, now)
        else:
            movement = self._maybe_walk(now, dt)
            if movement is not None:
                self._show_frame(movement, now)
            else:
                # Follow movement anywhere on the virtual desktop; after a
                # few seconds of stillness, go back to ordinary idle sprites.
                if now - self._last_pointer_move < 4.0:
                    look_direction = self._gaze_direction(pointer)
                else:
                    look_direction = None
                    self._gaze_sector = None
                if look_direction is not None:
                    self._show_frame("look", now, fixed=look_direction)
                elif (self.settings.observe_computer
                      and self.activity_monitor.latest().is_busy()):
                    self._show_frame("review", now)
                elif self.state.energy < 10 or self.state.mood < 10:
                    self._show_frame("failed", now)
                elif self.state.satiety < 20 or self.state.energy < 24:
                    self._show_frame("waiting", now)
                else:
                    self._show_frame("idle", now)
        if now >= self._next_idle_emote:
            self._next_idle_emote = now + random.uniform(85, 190)
            if (
                not self.state.sleeping
                and now >= self._action_until
                and self._walk_remaining == 0
                and (self.toolbar is None or not self.toolbar.visible)
            ):
                self._start_action(random.choice(("waiting", "review", "idle")), 1.6)
                self._idle_emote()
        if now >= self._next_comment:
            self._next_comment = now + random.uniform(175, 360)
            if (
                self.settings.spontaneous_talk
                and not self.state.sleeping
                and (self.toolbar is None or not self.toolbar.visible)
                and now - self._last_spoken >= 85
            ):
                activity_event = self.computer_voice.maybe_event(
                    self.activity_monitor.latest(), now,
                )
                if activity_event is not None:
                    response = self.mind.computer_event(
                        activity_event, self.state, self.context, now,
                    )
                else:
                    response = self.mind.spontaneous_event(
                        self.state, self.context, now,
                    )
                self._react(response, 3600)
        if self.toolbar is not None and self.toolbar.visible:
            self.toolbar.refresh()
        self._refresh_status()
        # Focus changes from browser voice input can reorder foreign topmost
        # windows. Repair only after an actual overlapping z-order loss.
        if now - self._last_stack_check >= 1.5:
            self._last_stack_check = now
            self._overlay_stack.maintain()
        if now - self._last_saved >= 55:
            self._save()
        if not self._closed:
            self._scheduled_tick = self.root.after(TICK_MILLISECONDS, self._tick)

    def _save(self) -> None:
        self.state.advance(
            time.time(), auto_routine=self.settings.auto_routine,
            allow_bedtime=self._allow_bedtime(),
            allow_nap=self._allow_nap(),
            interrupt_nap=self._interrupt_nap(),
            effort=self._live_effort(),
        )
        try:
            self.store.save(self.state, self.settings,
                            adaptive=self.adaptive.memory)
        except OSError as error:
            messagebox.showwarning(
                "Aiko", f"Spielstand konnte nicht gespeichert werden:\n{error}",
            )
        self._last_saved = time.monotonic()

    def quit(self) -> None:
        if self._closed:
            return
        self._closed = True
        for scheduled in (self._scheduled_tick, self._scheduled_greeting):
            if scheduled is not None:
                self.root.after_cancel(scheduled)
        self.activity_monitor.stop()
        self._save()
        self._cancel_followup()
        self._hide_bubble()
        if self.settings_popup is not None:
            self.settings_popup.close()
        if self.toolbar is not None:
            self.toolbar.close()
            self.toolbar = None
        if self.status_panel is not None:
            self.status_panel.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    load_env_file()
    app = DesktopPet()
    app.run()


if __name__ == "__main__":
    main()
