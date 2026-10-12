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
from tkinter import messagebox

from .adaptive import AdaptiveRoutine, Observation
from .application.commands import CareCommand
from .application.controller import CareController, CareRuntime
from .application.router import ApplicationRouter
from .animation import (
    FRAME_COUNTS, FRAME_TIMINGS as FRAME_TIMINGS,
    FrameClock, choose_passive_animation,
)
from .config import load_env_file
from .desktop_input import GlobalMouseClicks, idle_seconds_windows
from .dialogue import AikoMind, ComputerVoice, Reaction
from .gaze import gaze_sector
from .movement import WalkConditions, WalkController
from .routine import TimeContext, context_at
from .reaction_sequence import Cue, EMOTES
from .reaction_playback import ReactionPlayer, choose_idle_emote
from .storage import StateStore
from .system_activity import ActivityMonitor, workload_intensity
from .taskbar import TaskbarTrack, locate_primary_taskbar
from .window_stack import WindowStack
from .asset_paths import ASSETS, EMOTE_ASSETS, SCI_FI_UI as SCI_FI_UI
from .ui.action_toolbar import ActionToolbar
from .ui.settings_popup import SettingsPopup
from .ui.status_panel import StatusPanel

FRAME_WIDTH = 128
FRAME_HEIGHT = 208
TICK_MILLISECONDS = 140
MAGENTA = "#ff00ff"



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
        self._frame_clock = FrameClock(started_at=time.monotonic())
        self._last_tick = time.monotonic()
        self._last_track_check = self._last_tick
        self._action_until = 0.0
        self._action_state = "idle"
        self._movement = WalkController(
            next_walk_at=time.monotonic() + random.uniform(3.0, 8.0),
        )
        self._last_saved = time.monotonic()
        self.mind = AikoMind(started_at=self._last_saved)
        self.application = ApplicationRouter(
            CareController(self.state, self.mind, self.adaptive),
        )
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
        self._reaction_player = ReactionPlayer(
            schedule=self.root.after,
            cancel_timer=self.root.after_cancel,
            display_emote=self._show_emote,
            display_text=self.say,
            start_action=self._start_action,
            mark_spoken=self._mark_reaction_spoken,
            is_closed=lambda: self._closed,
        )
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
                    frame = frame.zoom(2)
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

    @property
    def _followup_timeout(self) -> str | None:
        """Compatibility view of the playback scheduler's pending timer."""
        return self._reaction_player.pending_timer

    @property
    def _speech_generation(self) -> int:
        return self._reaction_player.generation

    @property
    def _reaction_cues(self) -> tuple[Cue, ...]:
        return self._reaction_player.cues

    def _mark_reaction_spoken(self) -> None:
        self._last_spoken = time.monotonic()

    def _cancel_followup(self) -> None:
        """Cancel an older reaction, including every pending follow-up."""
        self._reaction_player.cancel()

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
        """Delegate the timeline; the GUI only renders visual effects."""
        self._reaction_player.play(
            reaction, duration_ms, animate=not self.state.sleeping,
        )

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
        if (
            self.toolbar is not None
            and self.toolbar.visible
            and not (over_ui or over_popup)
        ):
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
            and now - self._last_hover >= (
                2.0 if self.settings.toolbar_x is not None else 0.9
            )
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
        """Run a care command through the shared application boundary."""
        stamp = time.time()
        now = time.monotonic()
        result = self.application.dispatch(
            CareCommand.from_action(action),
            runtime=CareRuntime(
                wall_time=stamp,
                monotonic_time=now,
                auto_routine=self.settings.auto_routine,
                allow_bedtime=self._allow_bedtime(),
                allow_nap=self._allow_nap(),
                interrupt_nap=self._interrupt_nap(),
                effort=self._live_effort(),
            ),
        )
        self.context = result.context
        if result.reaction is None:
            # A fallback must not be overwritten by an older, queued aside.
            self._cancel_followup()
            self.say(result.fallback_text, 2450)
        else:
            self._react(result.reaction, 2900)
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
            self.status_panel.window.wm_attributes(
                "-topmost", self.settings.always_on_top,
            )
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
            self._emote_images[emote] = original.zoom(3)
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
        emote = choose_idle_emote(
            energy=self.state.energy,
            satiety=self.state.satiety,
            mood=self.state.mood,
            affection=self.state.affection,
        )
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

    @property
    def _walk_remaining(self) -> float:
        """Legacy control surface: walking state now belongs to WalkController."""
        return self._movement.remaining_distance

    @_walk_remaining.setter
    def _walk_remaining(self, value: float) -> None:
        self._movement.remaining_distance = value

    @property
    def _next_walk(self) -> float:
        return self._movement.next_walk_at

    @_next_walk.setter
    def _next_walk(self, value: float) -> None:
        self._movement.next_walk_at = value

    def _maybe_walk(self, now: float, dt: float) -> str | None:
        """Apply a planned horizontal step; only Tkinter moves the window."""
        observed = self.adaptive.current
        busy = (observed.focused if observed is not None
                else self.activity_monitor.latest().is_busy())
        conditions = WalkConditions(
            now=now,
            elapsed_seconds=dt,
            x=self.settings.x or 0,
            track=self.track,
            sprite_width=self.width,
            energy=self.state.energy,
            auto_walk=self.settings.auto_walk,
            sleeping=self.state.sleeping,
            attention_active=now < self._attention_until,
            toolbar_visible=self.toolbar is not None and self.toolbar.visible,
            observing_computer=self.settings.observe_computer,
            computer_busy=busy,
            quiet_period=bool(observed is not None and observed.quiet),
        )
        step = self._movement.plan_step(conditions)
        if step is None:
            return None
        old_x = self.settings.x or 0
        self._place_x(old_x + step.pixels)
        displacement = (self.settings.x or 0) - old_x
        if self._movement.record_displacement(displacement):
            if (
                self.settings.spontaneous_talk
                and now - self._last_spoken > 130
                and random.random() < 0.23
            ):
                self._react(self.mind.say_event(
                    "walk_pause", self.state, self.context, now,
                ))
        return step.animation

    def _show_frame(self, state: str, now: float, *, fixed: int | None = None) -> None:
        """Render the next chosen frame without owning animation timing."""
        frames = self.sprites[state]
        frame_index = self._frame_clock.next_index(
            state, now, len(frames), fixed=fixed,
        )
        self.canvas.itemconfigure(self.image_item, image=frames[frame_index])

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
        if (
            now - observed_at > 25
            or not self.settings.spontaneous_talk
            or self.state.sleeping
        ):
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

    def _advance_pet_lifecycle(self, now: float, wall_time: float) -> None:
        """Apply the elapsed care simulation and period-change reactions."""
        was_sleeping = self.state.sleeping
        previous_period = (self.context.day_key, self.context.period)
        self._observe_adaptive(now, wall_time)
        self.state.advance(
            wall_time, auto_routine=self.settings.auto_routine,
            allow_bedtime=self._allow_bedtime(),
            allow_nap=self._allow_nap(),
            interrupt_nap=self._interrupt_nap(),
            effort=self._live_effort(),
        )
        self.context = context_at(wall_time)
        current_period = (self.context.day_key, self.context.period)
        if current_period != previous_period:
            if self.toolbar is not None:
                self.toolbar.refresh()
            if self.settings.spontaneous_talk and self.state.sleeping != was_sleeping:
                event = "sleep" if self.state.sleeping else "wake"
                self._react(self.mind.say_event(event, self.state, self.context, now))

    def _refresh_taskbar_track(self, now: float) -> None:
        """Reposition Aiko only when taskbar geometry actually changes."""
        if now - self._last_track_check >= 4.0:
            self._last_track_check = now
            new_track = locate_primary_taskbar(
                self.root.winfo_screenwidth(), self.root.winfo_screenheight(),
            )
            if new_track != self.track:
                self.track = new_track
                self._place_x(self.settings.x or self.track.left)

    def _render_current_sprite(
        self, now: float, elapsed_seconds: float, pointer: tuple[int, int],
    ) -> None:
        """Choose a movement/action/passive sprite, then render its frame."""
        if self.state.sleeping:
            self._walk_remaining = 0
            self._show_frame("idle", now, fixed=2)
        elif now < self._action_until:
            self._show_frame(self._action_state, now)
        else:
            movement = self._maybe_walk(now, elapsed_seconds)
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
                # Keep hardware sampling lazy: looking at the cursor has
                # precedence and previously skipped this monitor read.
                computer_busy = (
                    self.activity_monitor.latest().is_busy()
                    if look_direction is None and self.settings.observe_computer
                    else False
                )
                animation = choose_passive_animation(
                    gaze_direction=look_direction,
                    observing_computer=self.settings.observe_computer,
                    computer_busy=computer_busy,
                    energy=self.state.energy,
                    mood=self.state.mood,
                    satiety=self.state.satiety,
                )
                self._show_frame(
                    animation.animation, now, fixed=animation.fixed_frame,
                )

    def _maybe_show_idle_emote(self, now: float) -> None:
        """Run occasional nonverbal reactions only while Aiko is free."""
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

    def _maybe_speak_spontaneously(self, now: float) -> None:
        """Run the next spontaneous dialogue slot without interrupting care."""
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

    def _present_pending_notification(self, now: float) -> None:
        """Drain at most one external event without interrupting Aiko.

        Only this Tk event-loop method may turn queued notification data into
        desktop widgets. Untrusted senders cannot call this renderer directly.
        """
        if (
            self.state.sleeping
            or now < self._action_until
            or now - self._last_spoken < 3
            or self._bubble is not None
            or self.settings_popup is not None
            or (self.toolbar is not None and self.toolbar.visible)
        ):
            return
        notification = self.application.next_notification()
        if notification is None:
            return
        self.say(f"{notification.title}: {notification.message}", 3500)
        self._last_spoken = now

    def _refresh_overlays_and_autosave(self, now: float) -> None:
        """Refresh visible panels, window layering and periodic persistence."""
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

    def _tick(self) -> None:
        """Coordinate one desktop update; behavior is owned by small methods."""
        if self._closed:
            return
        # A manual test refresh must not create a second scheduled timer.
        if self._scheduled_tick is not None:
            self.root.after_cancel(self._scheduled_tick)
            self._scheduled_tick = None
        now = time.monotonic()
        dt = max(0.0, min(0.5, now - self._last_tick))
        self._last_tick = now
        stamp = time.time()
        self._advance_pet_lifecycle(now, stamp)
        self._refresh_taskbar_track(now)
        self._poll_desktop_click()
        self._refresh_hover(now)
        self._react_to_computer(now)
        pointer = self._observe_pointer(now)
        self._render_current_sprite(now, dt, pointer)
        self._maybe_show_idle_emote(now)
        self._maybe_speak_spontaneously(now)
        self._present_pending_notification(now)
        self._refresh_overlays_and_autosave(now)
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
        self.application.close()
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
