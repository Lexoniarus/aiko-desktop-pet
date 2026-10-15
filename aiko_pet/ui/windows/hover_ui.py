"""Own toolbar visibility and independent utility-window lifetimes."""

from __future__ import annotations

import time
import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from ...application.settings import SettingKey
from ...games.rock_paper_scissors import Score
from ..common.skin import AikoSkin
from ..view_models.contracts import (
    HoverAnchor,
    HoverSnapshot,
    SettingsSnapshot,
    StatusSnapshot,
)
from ..view_models.food_models import FoodChoice, FoodChoiceId
from .action_toolbar import ActionToolbar
from .food_menu import FoodMenu
from .game_speech import GameSpeech
from .hover_contracts import HoverActions
from .rock_paper_scissors_window import RockPaperScissorsWindow
from .settings_contracts import SettingsActions
from .settings_window import SettingsWindow


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
    set_option: Callable[[SettingKey, bool], None]
    toggle_scale: Callable[[], None]
    forget_rhythm: Callable[[], None]
    reset_toolbar: Callable[[], None]
    center: Callable[[], None]
    quit: Callable[[], None]
    move_speech: Callable[[], None]
    restore_stack: Callable[[], bool]
    always_on_top: Callable[[], bool]
    game_speech: GameSpeech
    food_choices: tuple[FoodChoice, ...]
    feed: Callable[[FoodChoiceId], None] | None = None
    game_completed: Callable[[Score], object] | None = None


class HoverUi:
    """One visibility owner; an open utility window is not a modal menu."""

    def __init__(
        self, root: tk.Tk, canvas: tk.Canvas, ports: HoverUiPorts,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self._ports = ports
        self._skin = AikoSkin(root)
        self.toolbar: ActionToolbar | None = None
        self.settings_window: SettingsWindow | None = None
        self.game_window: RockPaperScissorsWindow | None = None
        self.food_menu: FoodMenu | None = None
        self._settings_position: tuple[int, int] | None = None
        self._keep_open = False
        self.last_hover = -100.0

    @property
    def keep_open(self) -> bool:
        """Session-local visibility pin, independent of position and topmost."""
        return self._keep_open

    @property
    def game_open(self) -> bool:
        return self.game_window is not None

    @property
    def settings_engaged(self) -> bool:
        window = self.settings_window
        return window is not None and window.interacting(
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
            time.monotonic(),
        )

    @property
    def interaction_active(self) -> bool:
        """Mapped/pinned windows alone must not suppress autonomous behavior."""
        toolbar = self.toolbar
        using_toolbar = toolbar is not None and toolbar.visible and (
            toolbar.dragging or not self._keep_open
            or self.pointer_inside(
                self.root.winfo_pointerx(), self.root.winfo_pointery(),
            )
        )
        menu = self.food_menu
        using_food = menu is not None and menu.contains_pointer(
            self.root.winfo_pointerx(), self.root.winfo_pointery(),
        )
        return bool(using_toolbar or using_food or self.settings_engaged)

    def _interact(self, action: str) -> None:
        if action == "play":
            self.open_game()
        elif action == "feed" and self._ports.feed is not None:
            self.open_food_menu()
        elif not self.game_open:
            self._ports.care(action)

    def _food_menu_closed(self) -> None:
        self.food_menu = None

    def _food_selected(self, food_id: FoodChoiceId) -> None:
        if self._ports.feed is not None and not self.game_open:
            self._ports.feed(food_id)

    def open_food_menu(self) -> None:
        """Reuse one selection window; no domain mutations before choice."""
        if self.game_open:
            return
        if self.food_menu is not None:
            self.food_menu.focus()
            return
        toolbar = self.toolbar
        x = toolbar.window.winfo_rootx() if toolbar is not None else 200
        y = (
            toolbar.window.winfo_rooty() + toolbar.window.winfo_height()
            if toolbar is not None else 200
        )
        self.food_menu = FoodMenu(
            self.root, x, y, choices=self._ports.food_choices,
            selected=self._food_selected, closed=self._food_menu_closed,
            always_on_top=self._ports.always_on_top(), skin=self._skin,
        )
        self._ports.restore_stack()

    def close_food_menu(self) -> None:
        if self.food_menu is not None:
            self.food_menu.close()

    def _game_closed(self, completed: Score) -> None:
        """Pass real rounds to the application, then clear the transient UI."""
        try:
            if completed.games and self._ports.game_completed is not None:
                self._ports.game_completed(completed)
        finally:
            self.game_window = None
            self._ports.game_speech.stop()
            self.last_hover = time.monotonic()
            self._set_care_buttons_enabled(True)
            if self.toolbar is not None:
                self.toolbar.refresh()
            self.refresh_status()

    def _set_care_buttons_enabled(self, enabled: bool) -> None:
        if self.toolbar is None:
            return
        for name, button in self.toolbar.buttons.items():
            if name != "play":
                button.configure(state="normal" if enabled else "disabled")

    def open_game(self) -> None:
        if self.game_window is not None:
            self.game_window.focus()
            self._ports.restore_stack()
            return
        self.close_food_menu()
        self._ports.game_speech.start()
        try:
            self.game_window = RockPaperScissorsWindow(
                self.root, on_closed=self._game_closed,
                speak=self._ports.game_speech.say,
                emote=self._ports.game_speech.emote,
                hand=self._ports.game_speech.hand,
                animate=self._ports.game_speech.animate,
                always_on_top=self._ports.always_on_top(),
                skin=self._skin,
            )
        except Exception:
            self._ports.game_speech.stop()
            raise
        self._set_care_buttons_enabled(False)
        self.game_window.greet()
        self._ports.restore_stack()

    def close_game(self) -> None:
        if self.game_window is not None:
            self.game_window.close()

    def show_toolbar(self) -> None:
        if self.toolbar is None:
            self.toolbar = ActionToolbar(
                self.root, snapshot=self._ports.hover_snapshot,
                status_snapshot=self._ports.status_snapshot,
                anchor=self._ports.anchor,
                actions=HoverActions(
                    interact=self._interact, toggle_pin=self.toggle_pin,
                    open_settings=self.open_settings,
                    save_position=self._ports.save_position,
                    move_speech=self._ports.move_speech,
                    restore_stack=self._ports.restore_stack,
                ),
                always_on_top=self._ports.always_on_top(), skin=self._skin,
            )
        self.toolbar.set_pinned(self._keep_open)
        self.toolbar.show()
        self._set_care_buttons_enabled(not self.game_open)

    def note_sprite_hover(self, now: float) -> None:
        """Keep hover timing with the owner of toolbar visibility."""
        self.last_hover = now

    def toggle_pin(self) -> None:
        self._keep_open = not self._keep_open
        self.last_hover = time.monotonic()
        self.show_toolbar()

    def open_status(self) -> None:
        """F2 reveals and pins the same toolbar, never a second status window."""
        self._keep_open = True
        self.show_toolbar()
        if self.toolbar is not None:
            self.toolbar.focus()
        self._ports.restore_stack()

    def _settings_closed(self) -> None:
        if self.settings_window is not None:
            self._settings_position = self.settings_window.position
        self.settings_window = None

    def open_settings(self, x: int, y: int) -> None:
        if self.settings_window is not None:
            self.settings_window.refresh()
            self.settings_window.focus()
            self._ports.restore_stack()
            return
        self.settings_window = SettingsWindow(
            self.root, x, y, snapshot=self._ports.settings_snapshot,
            actions=SettingsActions(
                toggle_scale=self._ports.toggle_scale,
                set_option=self._ports.set_option,
                forget_rhythm=self._ports.forget_rhythm,
                reset_toolbar=self._ports.reset_toolbar,
                center=self._ports.center, quit=self._ports.quit,
                closed=self._settings_closed,
            ),
            always_on_top=self._ports.always_on_top(),
            skin=self._skin, position=self._settings_position,
        )
        self.settings_window.focus()
        self._ports.restore_stack()

    def close_settings(self) -> None:
        if self.settings_window is not None:
            self.settings_window.close()

    def set_topmost(self, enabled: bool) -> None:
        for window in (
            self.toolbar, self.settings_window, self.game_window,
            self.food_menu,
        ):
            if window is not None:
                window.window.wm_attributes("-topmost", enabled)

    def refresh_status(self) -> None:
        """Status is now an optional section of the existing toolbar."""
        if self.toolbar is not None:
            self.toolbar.refresh_details()

    def refresh_settings(self) -> None:
        if self.settings_window is not None:
            self.settings_window.refresh()

    def pointer_inside(self, x: int, y: int) -> bool:
        widget = self.root.winfo_containing(x, y)
        over_sprite = widget is self.root or widget is self.canvas
        toolbar = self.toolbar
        over_toolbar = toolbar is not None and (
            toolbar.contains_pointer(x, y) or toolbar.contains_bridge(x, y)
        )
        return bool(over_sprite or over_toolbar)

    def _auto_hide_toolbar(self) -> None:
        toolbar = self.toolbar
        if toolbar is not None and not self._keep_open and not toolbar.dragging:
            toolbar.hide()

    def dismiss_outside(self, x: int, y: int) -> None:
        """Outside clicks dismiss only transient controls, never settings."""
        menu = self.food_menu
        if menu is not None and not menu.contains_pointer(x, y):
            if not self.pointer_inside(x, y):
                menu.close()
        if not self.pointer_inside(x, y):
            self._auto_hide_toolbar()

    def refresh_hover(self, now: float) -> None:
        toolbar = self.toolbar
        if toolbar is not None and toolbar.dragging:
            self.last_hover = now
            return
        x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
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
            self._auto_hide_toolbar()

    def close_toolbar(self) -> None:
        self.close_food_menu()
        if self.toolbar is not None:
            self.toolbar.close()
            self.toolbar = None
        self._keep_open = False
