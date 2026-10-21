"""Own toolbar visibility and independent utility-window lifetimes."""

from __future__ import annotations

import time
import tkinter as tk
from dataclasses import dataclass
from typing import Callable

from ...application.settings import SettingKey
from ...application.social_content import PreparedSocialContent, SocialCategory
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from ..view_models.contracts import (
    HoverAnchor,
    HoverSnapshot,
    SettingsSnapshot,
    StatusSnapshot,
)
from ..view_models.credits import project_credits
from ..view_models.food_models import FoodChoice, FoodChoiceId
from .action_toolbar import ActionToolbar
from .blackjack_window import BlackjackWindow
from .food_menu import FoodMenu
from .game_contracts import GameCardPorts, GameWindow
from .game_menu import GameMenu
from .game_speech import GameSpeech
from .hover_contracts import HoverActions
from .rock_paper_scissors_window import RockPaperScissorsWindow
from .settings_contracts import SettingsActions
from .settings_window import SettingsWindow
from .social_menu import SocialMenu
from .tic_tac_toe_window import TicTacToeWindow


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
    place_item: Callable[[FoodChoiceId], None] | None = None
    can_place_item: Callable[[], bool] = lambda: True
    game_completed: Callable[[SessionSummary], object] | None = None
    game_round: Callable[[GameRoundEvent], None] = lambda _event: None
    defer_game: Callable[[Callable[[], None]], None] | None = None
    game_dialogue: Callable[[str], str] | None = None
    can_interact: Callable[[str], bool] = lambda _action: True
    game_ready: Callable[[], bool] = lambda: True
    cards: GameCardPorts | None = None
    game_bounds_at: BoundsAt | None = None
    social_selected: Callable[[SocialCategory], None] | None = None
    social_cancel: Callable[[], None] = lambda: None
    social_enabled: Callable[[], bool] = lambda: False
    social_snapshot: Callable[[], tuple[str, PreparedSocialContent | None]] = lambda: (
        "",
        None,
    )


class HoverUi:
    """One visibility owner; an open utility window is not a modal menu."""

    def __init__(
        self,
        root: tk.Tk,
        canvas: tk.Canvas,
        ports: HoverUiPorts,
        *, skin: AikoSkin | None = None,
    ) -> None:
        self.root = root
        self.canvas = canvas
        self._ports = ports
        self._skin = skin if skin is not None else AikoSkin(root)
        self.toolbar: ActionToolbar | None = None
        self.settings_window: SettingsWindow | None = None
        self.game_window: GameWindow | None = None
        self.food_menu: FoodMenu | None = None
        self.game_menu: GameMenu | None = None
        self.social_menu: SocialMenu | None = None
        self._pending_game: object | None = None
        self._settings_position: tuple[int, int] | None = None
        self._keep_open = False
        self.last_hover = -100.0

    @property
    def keep_open(self) -> bool:
        """Session-local visibility pin, independent of position and topmost."""
        return self._keep_open

    @property
    def game_open(self) -> bool:
        return self.game_window is not None or self._pending_game is not None

    @property
    def control_windows(self) -> tuple[tk.Toplevel, ...]:
        """Back-to-front transient controls; settings remain above speech."""
        windows = [self.toolbar.window] if self.toolbar and self.toolbar.visible else []
        if self.game_window is not None:
            windows.append(self.game_window.window)
        return tuple(windows)

    @property
    def settings_engaged(self) -> bool:
        window = self.settings_window
        return window is not None and window.interacting(
            self.root.winfo_pointerx(),
            self.root.winfo_pointery(),
            time.monotonic(),
        )

    @property
    def menu_engaged(self) -> bool:
        """Menu use suppresses incidental chatter/wandering, not object actions."""
        toolbar = self.toolbar
        using_toolbar = (
            toolbar is not None
            and toolbar.visible
            and (
                toolbar.dragging
                or not self._keep_open
                or self.pointer_inside(
                    self.root.winfo_pointerx(),
                    self.root.winfo_pointery(),
                )
            )
        )
        return bool(
            using_toolbar
            or self.settings_engaged
            or toolbar is not None
            and toolbar.keyboard_engaged
        )

    def _interact(self, action: str) -> None:
        if action == "place_item":
            self.open_food_menu()
            return
        if action == "talk" and self._ports.social_selected is not None:
            self.open_social_menu()
            return
        self.close_social_menu()
        if action == "play":
            self.open_game_menu()
        elif not self.game_open and self._ports.can_interact(action):
            self._ports.care(action)

    def _food_menu_closed(self) -> None:
        self.food_menu = None
        if self.toolbar is not None:
            self.toolbar.close_selector()

    def _food_selected(self, food_id: FoodChoiceId) -> None:
        if self._ports.place_item is not None and self._ports.can_place_item():
            self._ports.place_item(food_id)

    def open_food_menu(self) -> None:
        """Reuse one embedded placement view; no domain mutations before choice."""
        if self._ports.place_item is None:
            return
        self.close_social_menu()
        self.close_game_menu()
        if self.food_menu is not None:
            self.food_menu.focus()
            return
        self.show_toolbar()
        assert self.toolbar is not None
        self.food_menu = FoodMenu(
            self.toolbar.selector_parent(self.close_food_menu),
            choices=self._ports.food_choices,
            selected=self._food_selected,
            closed=self._food_menu_closed,
            skin=self._skin,
            can_select=self._ports.can_place_item,
        )
        self.food_menu.focus()
        self._ports.restore_stack()

    def close_food_menu(self) -> None:
        if self.food_menu is not None:
            self.food_menu.close()

    def _game_closed(self, completed: SessionSummary) -> None:
        """Pass real rounds to the application, then clear the transient UI."""
        try:
            if self._ports.game_completed is not None:
                self._ports.game_completed(completed)
        finally:
            self.game_window = None
            try:
                if self._ports.cards is not None:
                    self._ports.cards.clear()
            finally:
                self._ports.game_speech.stop()
            self.last_hover = time.monotonic()
            if self.toolbar is not None:
                self.toolbar.refresh()
            self.refresh_status()

    def close_game_menu(self) -> None:
        if self.game_menu is not None:
            self.game_menu.close()

    def _game_menu_closed(self) -> None:
        self.game_menu = None
        if self.toolbar is not None:
            self.toolbar.close_selector()

    def open_game_menu(self) -> None:
        if self.game_open:
            return
        self.close_social_menu()
        if self.game_menu is not None:
            self.game_menu.focus()
            return
        self.close_food_menu()
        self.show_toolbar()
        assert self.toolbar is not None
        self.game_menu = GameMenu(
            self.toolbar.selector_parent(self.close_game_menu),
            choices=(GameId.ROCK_PAPER_SCISSORS,)
            + ((GameId.BLACKJACK,) if self._ports.cards is not None else ())
            + (GameId.TIC_TAC_TOE,),
            selected=self.open_game,
            closed=self._game_menu_closed,
            skin=self._skin,
            can_select=lambda: not self.game_open and self._ports.can_interact("play"),
        )
        self.game_menu.focus()
        self._ports.restore_stack()

    def open_game(self, game_id: GameId) -> None:
        if self.game_open or not self._ports.can_interact("play"):
            return
        self.close_social_menu()
        if not isinstance(game_id, GameId):
            raise ValueError("Game is not available")
        self.close_game_menu()
        token = object()
        self._pending_game = token
        try:
            if self._ports.defer_game is not None:
                self._ports.defer_game(lambda: self._open_game_now(game_id, token))
            else:
                self._open_game_now(game_id, token)
        except Exception:
            self._pending_game = None
            raise

    def _open_game_now(self, game_id: GameId, token: object) -> None:
        if self._pending_game is not token:
            return
        self._pending_game = None
        if self.game_window is not None or not self._ports.game_ready():
            return
        self.close_food_menu()
        self._ports.game_speech.start()
        try:
            if game_id is GameId.BLACKJACK:
                if self._ports.cards is None:
                    raise RuntimeError("Card presentation is unavailable")
                self.game_window = BlackjackWindow(
                    self.root,
                    on_closed=self._game_closed,
                    cards=self._ports.cards,
                    dialogue=self._ports.game_dialogue,
                    round_event=self._ports.game_round,
                    speak=self._ports.game_speech.say,
                    animate=self._ports.game_speech.animate,
                    always_on_top=self._ports.always_on_top(),
                    skin=self._skin,
                    bounds_at=self._ports.game_bounds_at,
                )
            elif game_id is GameId.TIC_TAC_TOE:
                self.game_window = TicTacToeWindow(
                    self.root,
                    on_closed=self._game_closed,
                    dialogue=self._ports.game_dialogue,
                    round_event=self._ports.game_round,
                    speak=self._ports.game_speech.say,
                    animate=self._ports.game_speech.animate,
                    always_on_top=self._ports.always_on_top(),
                    skin=self._skin,
                    bounds_at=self._ports.game_bounds_at,
                )
            else:
                self.game_window = self._create_rps()
            self.game_window.greet()
            self._ports.restore_stack()
        except Exception:
            if self.game_window is not None:
                self.game_window.close()
            else:
                try:
                    if self._ports.cards is not None:
                        self._ports.cards.clear()
                finally:
                    self._ports.game_speech.stop()
            raise
        if self.toolbar is not None:
            self.toolbar.refresh_actions()

    def _create_rps(self) -> RockPaperScissorsWindow:
        return RockPaperScissorsWindow(
            self.root,
            on_closed=self._game_closed,
            dialogue=self._ports.game_dialogue,
            round_event=self._ports.game_round,
            speak=self._ports.game_speech.say,
            emote=self._ports.game_speech.emote,
            hand=self._ports.game_speech.hand,
            animate=self._ports.game_speech.animate,
            always_on_top=self._ports.always_on_top(),
            skin=self._skin,
            bounds_at=self._ports.game_bounds_at,
        )

    def close_game(self) -> None:
        self._pending_game = None
        self.close_game_menu()
        if self.game_window is not None:
            self.game_window.close()
        elif self._ports.cards is not None:
            self._ports.cards.clear()

    def open_social_menu(self) -> None:
        if self.game_open:
            return
        if self.social_menu is not None:
            self.social_menu.focus()
            return
        self.close_food_menu()
        self.close_game_menu()
        self.show_toolbar()
        assert self.toolbar is not None
        self.social_menu = SocialMenu(
            self.toolbar.selector_parent(self.close_social_menu),
            selected=self._social_selected,
            closed=self._social_menu_closed,
            enabled=self._ports.social_enabled,
            can_interact=lambda: self._ports.can_interact("talk"),
            snapshot=self._ports.social_snapshot,
            skin=self._skin,
        )
        self.social_menu.focus()
        self._ports.restore_stack()

    def _social_selected(self, category: SocialCategory | None) -> None:
        if not self._ports.can_interact("talk"):
            return
        if category is None:
            self.close_social_menu()
            self._ports.care("talk")
        elif self._ports.social_selected is not None:
            self._ports.social_selected(category)

    def _social_menu_closed(self) -> None:
        self.social_menu = None
        if self.toolbar is not None:
            self.toolbar.close_selector()
        self._ports.social_cancel()

    def close_social_menu(self) -> None:
        if self.social_menu is not None:
            self.social_menu.close()

    def show_toolbar(self) -> None:
        if self.toolbar is None:
            self.toolbar = ActionToolbar(
                self.root,
                snapshot=self._ports.hover_snapshot,
                status_snapshot=self._ports.status_snapshot,
                food_choices=self._ports.food_choices,
                anchor=self._ports.anchor,
                actions=HoverActions(
                    interact=self._interact,
                    toggle_pin=self.toggle_pin,
                    open_settings=self.open_settings,
                    save_position=self._ports.save_position,
                    move_speech=self._ports.move_speech,
                    restore_stack=self._ports.restore_stack,
                    can_interact=self._ports.can_interact,
                    can_place_item=self._ports.can_place_item,
                ),
                always_on_top=self._ports.always_on_top(),
                skin=self._skin,
            )
        self.toolbar.set_pinned(self._keep_open)
        self.toolbar.show()
        self.toolbar.refresh_actions()

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
            self.root,
            x,
            y,
            snapshot=self._ports.settings_snapshot,
            actions=SettingsActions(
                toggle_scale=self._ports.toggle_scale,
                set_option=self._ports.set_option,
                forget_rhythm=self._ports.forget_rhythm,
                reset_toolbar=self._ports.reset_toolbar,
                center=self._ports.center,
                quit=self._ports.quit,
                closed=self._settings_closed,
            ),
            always_on_top=self._ports.always_on_top(),
            skin=self._skin,
            position=self._settings_position,
            credits_snapshot=lambda: project_credits(self._ports.social_snapshot()[1]),
        )
        self.settings_window.focus()
        self._ports.restore_stack()

    def close_settings(self) -> None:
        if self.settings_window is not None:
            self.settings_window.close()

    def set_topmost(self, enabled: bool) -> None:
        if self._ports.cards is not None:
            self._ports.cards.set_topmost(enabled)
        for window in (
            self.toolbar,
            self.settings_window,
            self.game_window,
        ):
            if window is not None:
                window.window.wm_attributes("-topmost", enabled)

    def refresh_toolbar(self) -> None:
        if self.toolbar is not None:
            self.toolbar.refresh()

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
        # Focus checks and global polling can replay the menu-opening click.
        if self.pointer_inside(x, y):
            return
        menu = self.food_menu
        if self.social_menu is not None and not self.social_menu.contains_pointer(x, y):
            self.close_social_menu()
        if self.game_menu is not None and not self.game_menu.contains_pointer(x, y):
            self.close_game_menu()
        if menu is not None and not menu.contains_pointer(x, y):
            menu.close()
        self._auto_hide_toolbar()

    def refresh_hover(self, now: float) -> None:
        if self.settings_window is not None:
            self.settings_window.refresh_credits()
        for menu in (self.food_menu, self.game_menu, self.social_menu):
            if menu is not None:
                menu.refresh()
        toolbar = self.toolbar
        if toolbar is not None:
            toolbar.refresh_actions()
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
        elif (
            toolbar is not None
            and toolbar.visible
            and (
                now - self.last_hover
                >= (2.0 if self._ports.anchor().pinned_x is not None else 0.9)
            )
        ):
            self._auto_hide_toolbar()

    def close_toolbar(self) -> None:
        self.close_social_menu()
        self.close_food_menu()
        self.close_game_menu()
        if self.toolbar is not None:
            self.toolbar.close()
            self.toolbar = None
        self._keep_open = False
