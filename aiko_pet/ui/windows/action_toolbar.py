"""Single VN care/status window; HoverUi retains visibility and admission."""

from __future__ import annotations

import sys
import tkinter as tk
from functools import partial
from typing import Callable

from ...pet.content import GERMAN_TEXT
from ..common.description_tip import DescriptionTip
from ..common.image_button import ImageButton
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.status_readout import StatusReadout
from ..common.window_drag import WindowDrag
from ..view_models.contracts import HoverAnchor, HoverSnapshot, StatusSnapshot
from ..view_models.food_models import FoodChoice
from .hover_contracts import HoverActions
from .hover_geometry import HoverGeometry, Rect
from .moodlet_strip import MoodletStrip
from .toolbar_details import ToolbarDetails
from .wish_panel import WishPanel


class ActionToolbar:
    READOUTS = (
        ("mood", GERMAN_TEXT.format("status.mood"), "detail_wellbeing"),
        ("satiety", GERMAN_TEXT.format("need.satiety"), "status_satiety"),
        ("fun", GERMAN_TEXT.format("need.fun"), "status_fun"),
        ("energy", GERMAN_TEXT.format("need.energy"), "status_energy"),
        ("social", GERMAN_TEXT.format("need.social"), "status_social"),
        ("affection", GERMAN_TEXT.format("need.affection"), "status_affection"),
        ("friendship", GERMAN_TEXT.format("status.friendship"), "status_friendship"),
    )

    def __init__(
        self,
        root: tk.Tk,
        *,
        snapshot: Callable[[], HoverSnapshot],
        anchor: Callable[[], HoverAnchor],
        actions: HoverActions,
        always_on_top: bool,
        skin: AikoSkin | None = None,
        status_snapshot: Callable[[], StatusSnapshot] | None = None,
        food_choices: tuple[FoodChoice, ...] = (),
    ) -> None:
        self.root, self._snapshot, self._anchor, self._actions = (
            root,
            snapshot,
            anchor,
            actions,
        )
        self.skin = skin if skin is not None else AikoSkin(root)
        self.font_family = self.skin.font
        self.window = tk.Toplevel(root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=self.skin.border)
        self.window.wm_attributes("-topmost", always_on_top)
        if sys.platform == "win32":
            self.window.wm_attributes("-toolwindow", True)
        self.outer = self.skin.frame(self.window)
        self.outer.pack(fill="both", expand=True, padx=1, pady=1)
        title = tk.Frame(self.outer, bg=self.skin.title)
        title.pack(fill="x")
        self.today = self.skin.header(title, GERMAN_TEXT.format("vn.brand"))
        self.today.pack(side="left")
        self.settings_button = self.skin.button(
            title,
            "",
            self._open_settings,
            size="small",
            icon=self.skin.images.icon("ui_settings", 24),
        )
        self.settings_button.pack(side="right", padx=8, pady=4)
        self._drag = WindowDrag(
            self.window,
            self.today,
            moved=actions.move_speech,
            dropped=self._drag_dropped,
        )
        footer = tk.Frame(self.outer, bg=self.skin.background)
        footer.pack(side="bottom", fill="x", padx=10, pady=6)
        self.pin_button = self.skin.button(
            footer,
            "",
            actions.toggle_pin,
            size="footer",
            icon=self.skin.images.icon("ui_pin", 24),
        )
        self.pin_button.pack(side="left", padx=2)
        self.details_button = self.skin.button(
            footer,
            GERMAN_TEXT.format("ui.details_show"),
            self.toggle_details,
            size="footer",
        )
        self.details_button.pack(side="right", padx=2)
        body = ScrollRegion(
            self.outer,
            self.skin,
            width=660,
            height=min(790, max(240, root.winfo_screenheight() - 180)),
        )
        body.frame.pack(fill="both", expand=True)
        content = tk.Frame(body.body, bg=self.skin.background, padx=12, pady=10)
        content.pack(fill="both", expand=True)
        self.tips = DescriptionTip(self.outer, self.skin)
        summary = tk.Frame(
            content,
            bg=self.skin.panel,
            padx=8,
            pady=5,
            highlightthickness=1,
            highlightbackground=self.skin.border,
        )
        summary.pack(fill="x")
        copy = tk.Frame(summary, bg=self.skin.panel)
        copy.pack(side="left", fill="both", expand=True)
        self.emotion = tk.Label(
            copy,
            bg=self.skin.panel,
            fg=self.skin.text,
            font=(self.skin.font, 12, "bold"),
            anchor="w",
        )
        self.emotion.pack(fill="x")
        self.wellbeing = tk.Label(
            copy,
            bg=self.skin.panel,
            fg=self.skin.muted,
            font=(self.skin.font, 8),
            anchor="w",
        )
        self.wellbeing.pack(fill="x")
        self.readouts: dict[str, StatusReadout] = {}
        self.readouts["mood"] = StatusReadout(
            summary, self.skin, title=GERMAN_TEXT.format("status.mood"), width=176
        )
        self.readouts["mood"].frame.pack(side="right")
        self.moodlets = MoodletStrip(content, self.skin, self.tips)
        self.moodlets.frame.pack(fill="x", pady=(7, 0))
        self.wishes = WishPanel(
            content,
            self.skin,
            self.tips,
            {choice.id: choice.image_path for choice in food_choices},
        )
        self.wishes.frame.pack(fill="x", pady=(4, 8))
        care = tk.Frame(content, bg=self.skin.background)
        care.pack(fill="x")
        self.interaction_column = tk.Frame(
            care, bg=self.skin.background, width=254, height=348
        )
        self.interaction_column.pack(side="right", padx=(10, 0))
        self.interaction_column.pack_propagate(False)
        self.actions_frame = tk.Frame(self.interaction_column, bg=self.skin.background)
        self.actions_frame.pack(fill="both", expand=True)
        values = tk.Frame(care, bg=self.skin.background)
        values.pack(side="left", fill="both", expand=True)
        for key, text, icon in self.READOUTS[1:]:
            readout = StatusReadout(
                values, self.skin, title=text, icon=icon, friendship=key == "friendship"
            )
            readout.frame.pack(fill="x", pady=(0, 5), ipady=2)
            self.readouts[key] = readout
        self.buttons: dict[str, ImageButton] = {}
        for action, text, icon, submenu in (
            ("place_item", "ui.snack", "status_satiety", True),
            ("play", "ui.play", "status_fun", True),
            ("sleep", "ui.sleep_start", "action_sleep", False),
            ("talk", "ui.talk", "status_social", True),
            ("pet", "ui.pet", "action_pet", False),
        ):
            button = self.skin.button(
                self.actions_frame,
                GERMAN_TEXT.format(text) + ("  ›" if submenu else ""),
                partial(actions.interact, action),
                size="action",
                icon=self.skin.images.icon(icon, 24),
            )
            button.pack(pady=(0, 3))
            self.buttons[action] = button
        tk.Label(
            self.actions_frame,
            text=GERMAN_TEXT.format("vn.friendship_context"),
            wraplength=220,
            bg=self.skin.background,
            fg=self.skin.muted,
            font=(self.skin.font, 9),
            pady=8,
        ).pack(fill="x")
        self.hardware = self._context_label(content)
        self.workload = self._context_label(content)
        self.food_info = self._context_label(content)
        self.details = (
            ToolbarDetails(content, self.skin, status_snapshot)
            if status_snapshot is not None
            else None
        )
        self._details_open = False
        self.visible = False
        self._last_placement: tuple[int, int, int, int] | None = None
        self._selector_closed: Callable[[], None] | None = None
        self.window.bind("<Escape>", lambda _e: self.close_selector())
        body.adopt()

    def _context_label(self, parent: tk.Misc) -> tk.Label:
        label = tk.Label(
            parent,
            bg=self.skin.background,
            fg=self.skin.muted,
            font=(self.skin.font, 8),
            anchor="w",
            wraplength=620,
        )
        label.pack(fill="x", pady=2)
        return label

    @property
    def dragging(self) -> bool:
        return self._drag.dragging

    def set_pinned(self, enabled: bool) -> None:
        self.pin_button.set_selected(enabled)
        self.pin_button.configure(
            text=GERMAN_TEXT.format("ui.pin_release" if enabled else "ui.pin_keep")
        )

    def toggle_details(self) -> None:
        if self.details is None:
            return
        self.tips.hide()
        self._details_open = not self._details_open
        if self._details_open:
            self.details.refresh()
            self.details.frame.pack(fill="x", pady=(8, 0))
        else:
            self.details.frame.pack_forget()
        self.details_button.configure(
            text=GERMAN_TEXT.format(
                "ui.details_hide" if self._details_open else "ui.details_show"
            )
        )

    def refresh_details(self) -> None:
        if self._details_open and self.details is not None:
            self.details.refresh()

    def refresh_actions(self) -> None:
        for action, button in self.buttons.items():
            allowed = (
                self._actions.can_place_item()
                if action == "place_item"
                else self._actions.can_interact(action)
            )
            button.configure(state="normal" if allowed else "disabled")

    def _open_settings(self) -> None:
        self._actions.open_settings(
            self.window.winfo_rootx() + self.window.winfo_width(),
            self.window.winfo_rooty(),
        )

    def selector_parent(self, closed: Callable[[], None]) -> tk.Frame:
        self.close_selector()
        self.tips.hide()
        self.actions_frame.pack_forget()
        self._selector_closed = closed
        return self.interaction_column

    def close_selector(self) -> None:
        callback, self._selector_closed = self._selector_closed, None
        if callback is not None:
            callback()
        self.actions_frame.pack(fill="both", expand=True)

    def refresh(self) -> None:
        self.refresh_actions()
        view = self._snapshot()
        for widget, text in (
            (self.emotion, view.emotional.state_label),
            (self.wellbeing, view.wellbeing_line),
            (self.buttons["sleep"], view.sleep_label),
            (self.buttons["place_item"], view.feed_label + "  ›"),
            (self.hardware, view.hardware_line),
            (self.workload, view.workload_line),
            (self.food_info, view.food_line),
        ):
            if widget.cget("text") != text:
                widget.configure(text=text)
        for key, readout in self.readouts.items():
            suffix = (
                GERMAN_TEXT.format(
                    "ui.friendship_level_suffix", level=str(view.friendship_level)
                )
                if key == "friendship"
                else ""
            )
            readout.refresh(view.status_value(key), suffix=suffix)
        self.moodlets.refresh(view.emotional.moodlets)
        self.wishes.refresh(view.emotional.wishes)
        self.refresh_details()

    def contains_pointer(self, px: int, py: int) -> bool:
        if not self.visible:
            return False
        x, y = self.window.winfo_rootx(), self.window.winfo_rooty()
        return (
            x <= px < x + self.window.winfo_width()
            and y <= py < y + self.window.winfo_height()
        )

    def contains_bridge(self, px: int, py: int) -> bool:
        if not self.visible:
            return False
        anchor = self._anchor()
        return HoverGeometry.bridge(
            px,
            py,
            Rect(
                self.window.winfo_rootx(),
                self.window.winfo_rooty(),
                self.window.winfo_width(),
                self.window.winfo_height(),
            ),
            Rect(
                self.root.winfo_rootx(),
                self.root.winfo_rooty(),
                anchor.width,
                anchor.height,
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
            self._anchor(),
            width,
            height,
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        placement = x, y, width, height
        if placement != self._last_placement:
            self.window.geometry(f"+{x}+{y}")
            self._last_placement = placement

    def _drag_dropped(self, x: int, y: int) -> None:
        self._last_placement = (
            x,
            y,
            self.window.winfo_width(),
            self.window.winfo_height(),
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
        self.tips.hide()
        self.close_selector()
        self.window.withdraw()
        self._last_placement = None
        self._actions.move_speech()

    def close(self) -> None:
        self.tips.hide()
        self.close_selector()
        self._drag.close()
        self.window.destroy()
