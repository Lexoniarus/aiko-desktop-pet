"""The single movable care/status toolbar in the shared Kenney skin."""

from __future__ import annotations

import sys
import tkinter as tk
from functools import partial
from typing import Callable

from ...presentation.contracts import StatusSnapshot
from .hover_contracts import HoverActions, HoverAnchor, HoverSnapshot
from .hover_geometry import HoverGeometry, Rect
from ..common.skin import AikoSkin
from .toolbar_details import ToolbarDetails
from ..common.window_drag import WindowDrag


class ActionToolbar:
    """Render care, pin state and optional details; HoverUi owns visibility."""

    NEEDS = (
        ("satiety", "Sättigung", "#f5bd7a"),
        ("mood", "Laune", "#95ddc1"),
        ("energy", "Energie", "#98c9f5"),
        ("social", "Sozial", "#dda9ef"),
        ("affection", "Zuwendung", "#f0a5be"),
        ("friendship", "Freundschaft", "#ffb9c2"),
    )
    BAR_WIDTH = 92

    def __init__(
        self, root: tk.Tk, *, snapshot: Callable[[], HoverSnapshot],
        anchor: Callable[[], HoverAnchor], actions: HoverActions,
        always_on_top: bool, skin: AikoSkin | None = None,
        status_snapshot: Callable[[], StatusSnapshot] | None = None,
    ) -> None:
        self.root = root
        self._snapshot = snapshot
        self._anchor = anchor
        self._actions = actions
        self._current = snapshot()
        self.skin = skin if skin is not None else AikoSkin(root)
        self.font_family = self.skin.font
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=self.skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        outer = self.skin.frame(self.window)
        outer.pack(fill="both", expand=True, padx=3, pady=3)
        self.today = self.skin.header(outer, "")
        self.today.pack(fill="x")
        self._drag = WindowDrag(
            self.window, self.today, moved=actions.move_speech,
            dropped=self._drag_dropped,
        )
        needs_frame = tk.Frame(outer, bg=self.skin.background)
        needs_frame.pack(fill="x", padx=7, pady=(1, 5))
        self.needs: dict[str, tuple[tk.Canvas, int, tk.Label]] = {}
        for column in range(3):
            needs_frame.columnconfigure(column, weight=1, uniform="needs")
        for i, (key, _title, color) in enumerate(self.NEEDS):
            cell = tk.Frame(needs_frame, bg=self.skin.background)
            cell.grid(row=i // 3, column=i % 3, sticky="ew", padx=3, pady=2)
            label = tk.Label(
                cell, text="", font=(self.font_family, 9), width=20,
                fg=self.skin.text, bg=self.skin.background, anchor="w",
            )
            label.pack(anchor="w")
            bar = tk.Canvas(
                cell, width=self.BAR_WIDTH, height=10, bd=0,
                highlightthickness=0, bg="#969FB2",
            )
            rect = bar.create_rectangle(0, 0, 1, 10, outline="", fill=color)
            bar.pack(fill="x", pady=(3, 3))
            self.needs[key] = (bar, rect, label)
            bar.bind("<Configure>", partial(self._on_need_resize, key))
        actions_frame = tk.Frame(outer, bg=self.skin.background)
        actions_frame.pack(fill="x", padx=5)
        actions_row = tk.Frame(actions_frame, bg=self.skin.background)
        actions_row.pack(fill="x")
        extra_row = tk.Frame(actions_frame, bg=self.skin.background)
        extra_row.pack(fill="x")
        self.buttons: dict[str, tk.Button] = {}
        for action, title, parent in (
            ("feed", "Snack", actions_row),
            ("play", "Spielen", actions_row),
            ("pet", "Streicheln", actions_row),
            ("talk", "Reden", actions_row),
            ("sleep", "Schlafen", extra_row),
        ):
            self.buttons[action] = self._button(
                parent, title, partial(actions.interact, action),
            )
        self.pin_button = self._button(
            extra_row, "Offen halten", actions.toggle_pin,
        )
        self.settings_button = self._button(extra_row, "⋯", self._open_settings)
        self.hardware = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.skin.muted, bg=self.skin.background,
            anchor="w", padx=10, pady=3,
        )
        self.hardware.pack(fill="x")
        self.food_info = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.skin.muted, bg=self.skin.background,
            anchor="w", padx=10, pady=2,
        )
        self.food_info.pack(fill="x")
        self.workload = tk.Label(
            outer, text="", font=(self.font_family, 8),
            fg=self.skin.text, bg=self.skin.background,
            anchor="w", padx=10, pady=3,
        )
        self.workload.pack(fill="x")
        self.details: ToolbarDetails | None = None
        self.details_button: tk.Button | None = None
        self._details_open = False
        if status_snapshot is not None:
            self.details_button = self.skin.button(
                outer, "Details anzeigen", self.toggle_details, size="wide",
            )
            self.details_button.pack(anchor="w", padx=9, pady=(0, 4))
            self.details = ToolbarDetails(outer, self.skin, status_snapshot)
        self.visible = False
        self._last_placement: tuple[int, int, int, int] | None = None

    @property
    def dragging(self) -> bool:
        return self._drag.dragging

    def set_pinned(self, enabled: bool) -> None:
        """Display the controller's state without keeping a second pin flag."""
        self.pin_button.configure(
            text="Pin lösen" if enabled else "Offen halten",
            fg=self.skin.accent if enabled else self.skin.text,
        )

    def toggle_details(self) -> None:
        if self.details is None or self.details_button is None:
            return
        self._details_open = not self._details_open
        if self._details_open:
            self.details.refresh()
            self.details.frame.pack(fill="x", padx=9, pady=(0, 8))
        else:
            self.details.frame.pack_forget()
        self.details_button.configure(
            text="Details verbergen" if self._details_open else "Details anzeigen",
        )
        if self.visible:
            self.place()

    def refresh_details(self) -> None:
        if self._details_open and self.details is not None:
            self.details.refresh()

    def _button(
        self, parent: tk.Widget, text: str, command: Callable[[], None],
    ) -> tk.Button:
        size = "small" if text == "⋯" else "wide" if len(text) > 13 else "regular"
        button = self.skin.button(parent, text, command, size=size)
        button.pack(side="left", padx=2, pady=4)
        return button

    def _open_settings(self) -> None:
        button = self.settings_button
        self._actions.open_settings(
            button.winfo_rootx() + button.winfo_width(),
            button.winfo_rooty(),
        )

    def _on_need_resize(self, key: str, event: tk.Event) -> None:
        self._resize_need(key, event.width)

    def _resize_need(self, key: str, width: int | None = None) -> None:
        bar, rect, _label = self.needs[key]
        actual_width = width if width is not None else bar.winfo_width()
        if actual_width <= 1:
            actual_width = bar.winfo_reqwidth()
        amount = max(0.0, min(100.0, self._current.need_value(key)))
        bar.coords(rect, 0, 0, round(actual_width * amount / 100), 10)

    def refresh(self) -> None:
        view = self._snapshot()
        self._current = view
        changed = False
        for widget, value in (
            (self.buttons["sleep"], view.sleep_label),
            (self.buttons["feed"], view.feed_label),
            (self.today, view.header),
            (self.hardware, view.hardware_line),
            (self.workload, view.workload_line),
            (self.food_info, view.food_line),
        ):
            if widget.cget("text") != value:
                widget.configure(text=value)
                changed = True
        for key, title, _color in self.NEEDS:
            amount = max(0, min(100, view.need_value(key)))
            _bar, _rect, label = self.needs[key]
            text = f"{title}  {amount:.0f}%"
            if key == "friendship":
                text += f" · Lv {view.friendship_level}"
            if label.cget("text") != text:
                label.configure(text=text)
            self._resize_need(key)
        self.refresh_details()
        if changed and self.visible:
            self.place()

    def contains_pointer(self, px: int, py: int) -> bool:
        if not self.visible:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (x <= px < x + self.window.winfo_width()
                and y <= py < y + self.window.winfo_height())

    def contains_bridge(self, px: int, py: int) -> bool:
        if not self.visible:
            return False
        anchor = self._anchor()
        return HoverGeometry.bridge(
            px, py,
            Rect(
                self.window.winfo_rootx(), self.window.winfo_rooty(),
                self.window.winfo_width(), self.window.winfo_height(),
            ),
            Rect(
                self.root.winfo_rootx(), self.root.winfo_rooty(),
                anchor.width, anchor.height,
            ),
            pinned=anchor.pinned_x is not None,
        )

    def place(self) -> None:
        if self.dragging:
            return
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        x, y = HoverGeometry.placement(
            self._anchor(), width, height,
            self.root.winfo_screenwidth(), self.root.winfo_screenheight(),
        )
        placement = x, y, width, height
        if placement != self._last_placement:
            self.window.geometry(f"+{x}+{y}")
            self._last_placement = placement

    def _drag_dropped(self, x: int, y: int) -> None:
        self._last_placement = (
            x, y, self.window.winfo_width(), self.window.winfo_height(),
        )
        self._actions.save_position(x, y)

    def reset_position(self) -> None:
        self._actions.save_position(None, None)
        self._last_placement = None
        if self.visible:
            self.place()

    def show(self) -> None:
        if self.visible:
            return
        self.refresh()
        self.place()
        self.window.deiconify()
        self.visible = True
        self._actions.move_speech()
        self._actions.restore_stack()

    def focus(self) -> None:
        self.show()
        self.window.lift()
        self.window.focus_set()

    def hide(self) -> None:
        if not self.visible:
            return
        self.visible = False
        self.window.withdraw()
        self._last_placement = None
        self._actions.move_speech()

    def close(self) -> None:
        self._drag.close()
        self.window.destroy()
