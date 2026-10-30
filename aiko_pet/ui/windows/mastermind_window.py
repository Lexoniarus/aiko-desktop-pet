"""Ten prepared player rows; Aiko's concealed code stays on the desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.mastermind import ATTEMPTS, COLORS, PLACES, RoundView
from ...pet.content import GERMAN_TEXT
from ..common.image_button import update_button_state
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from .game_contracts import GameCodePorts
from .game_panel import GamePanel
from .game_presentation import GamePresentation
from .mastermind_drag import MastermindDrag
from .mastermind_finale import MastermindFinale
from .mastermind_sequence import MastermindSequence

ROW_HEIGHT = 48
HEADER_HEIGHT = 24
BOARD_HEIGHT = HEADER_HEIGHT + ATTEMPTS * ROW_HEIGHT
BOARD_PADDING = 6


class MastermindWindow:
    def __init__(
        self,
        root: tk.Tk,
        *,
        on_closed: Callable[[SessionSummary], None],
        codes: GameCodePorts,
        speak: Callable[[str, int], None],
        animate: Callable[[str], None],
        emote: Callable[[str, int], None],
        always_on_top: bool,
        skin: AikoSkin,
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        bounds_at: BoundsAt | None = None,
        presentation: GamePresentation | None = None,
        interrupt: Callable[[], None] = lambda: None,
    ) -> None:
        self._closed, self._busy = False, True
        self._on_closed, self._codes, self.skin = on_closed, codes, skin
        self._draft: list[str | None] = [None] * PLACES
        self._selected_color: str | None = None
        self._active, self._feedback_visible = 0, 4
        self._view = RoundView()
        self._sequence: MastermindSequence | None = None
        self._finale: MastermindFinale | None = None
        self._presentation = presentation
        self._layout_timer: str | None = None
        self._palette_images: dict[str, tk.PhotoImage] = {}
        self._drag = MastermindDrag(codes.images, self._drop, self._click_piece)
        self._panel = GamePanel(
            root,
            GERMAN_TEXT.format("game.name.mastermind"),
            close=self.close,
            next_round=self.next_round,
            skin=skin,
            always_on_top=always_on_top,
            game_id=GameId.MASTERMIND,
            bounds_at=bounds_at,
            body_height=780,
            reserve_right=120,
        )
        self.window = self._panel.window
        try:
            self._build(root, bounds_at)
            if presentation is not None:
                self._finale = MastermindFinale(
                    self.window, codes, presentation, topmost=always_on_top,
                )

            def say(text: str, milliseconds: int) -> None:
                speak(text, milliseconds)
                codes.move()

            self._sequence = MastermindSequence(
                schedule=self.window.after,
                cancel=self.window.after_cancel,
                present=self._present,
                show_code=codes.show,
                hide_code=codes.clear,
                say=say,
                animate=animate,
                emote=emote,
                dialogue=dialogue,
                round_event=round_event,
                express_event=express_event,
                finale=self._finale.play if self._finale else None,
                interrupt=interrupt, look=self._look_feedback,
            )
            self._present(self._sequence.game.view, self._sequence.game.score, True, 4)
            # These allocations may settle after the top-level Configure event.
            # Listen before show() so first mapping needs no click to finish.
            for widget in (self._panel.scroll.canvas, self.board_scroll.frame):
                widget.bind("<Configure>", self._configured, add="+")
            self._panel.show(root, prepare_body=self._fit_board)
            self._queue_layout()
            # Palette arrows edit the draft before inherited scroll bindings.
            tags = self.palette.bindtags()
            self.palette.bindtags((
                str(self.palette),
                *(t for t in tags if t != str(self.palette)),
            ))
            self.window.bind("<Configure>", self._configured, add="+")
        except Exception:
            self._closed = True
            if self._finale:
                self._finale.close()
            self._drag.cancel()
            self._cancel_layout()
            if self._sequence is not None:
                self._sequence.close()
            self._panel.destroy()
            self._palette_images.clear()
            codes.clear()
            raise

    def _label(self, text: str, size: int = 9) -> None:
        tk.Label(
            self._panel.body,
            text=text,
            wraplength=self._panel.content_width - 12,
            justify="left",
            bg=self.skin.background,
            fg=self.skin.text,
            font=(self.skin.font, size),
        ).pack(fill="x")

    def _build(self, root: tk.Tk, bounds_at: BoundsAt | None) -> None:
        self._label(GERMAN_TEXT.format('game.frontend.mm'), 11)
        self._label(GERMAN_TEXT.format("mastermind.rules"))
        compact = self._panel.content_width < 394
        self._palette_columns = 6
        self._palette_step = 40 if compact else 64
        self._palette_images = {
            color: self._codes.images.get(color).subsample(2)
            if compact
            else self._codes.images.get(color)
            for color in COLORS
        }
        self.palette = tk.Canvas(
            self._panel.body,
            width=self._palette_columns * self._palette_step,
            height=64 if compact else 74,
            highlightthickness=0,
            bg=self.skin.background,
            cursor="hand2",
            takefocus=True,
        )
        self.palette.pack(pady=4)
        self.palette.bind("<ButtonPress-1>", self._palette_press)
        for i, color in enumerate(COLORS):
            x, y = (
                i * self._palette_step + self._palette_step // 2,
                18 if compact else 28,
            )
            if color == "white":
                radius = 12 if compact else 22
                self.palette.create_oval(
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                    fill="#B5C3D4",
                    outline=self.skin.border,
                )
            self.palette.create_image(x, y, image=self._palette_images[color])
            label = GERMAN_TEXT.format(f"mastermind.color.{color}")
            separator = "\n" if compact else ": "
            self.palette.create_text(
                x,
                y + 29 if compact else y + 31,
                text=f"{i + 1}{separator}{label}",
                fill=self.skin.text,
                font=(self.skin.font, 8 if compact else 9),
            )
            self.palette.bind(str(i + 1), partial(self._key_color, color))
        self.palette.bind("<Left>", partial(self._key_slot, -1))
        self.palette.bind("<Right>", partial(self._key_slot, 1))
        self.palette.bind("<Delete>", lambda _event: self.clear_slot())
        self.palette.bind("<BackSpace>", lambda _event: self.clear_slot())
        self.palette.bind("<Return>", lambda _event: self.submit())
        actions = tk.Frame(self._panel.body, bg=self.skin.background)
        actions.pack(fill="x", pady=4)
        self.submit_button = self.skin.button(
            actions,
            GERMAN_TEXT.format("mastermind.submit"),
            self.submit,
            size="game_close" if compact else "game_next",
        )
        self.submit_button.pack(side="left")
        self.clear_button = self.skin.button(
            actions,
            GERMAN_TEXT.format("mastermind.clear"),
            self.clear_slot,
            size="menu_back" if compact else "game_close",
        )
        self.clear_button.pack(side="left", padx=6, pady=3)
        self._label(GERMAN_TEXT.format("mastermind.legend"), 8)
        screen_height = (
            bounds_at(root.winfo_rootx(), root.winfo_rooty()).height
            if bounds_at
            else root.winfo_screenheight()
        )
        self.board_scroll = ScrollRegion(
            self._panel.body,
            self.skin,
            width=min(470, self._panel.content_width - 10),
            height=min(BOARD_HEIGHT, max(144, screen_height - 560)),
            autohide=True,
        )
        self.board_scroll.frame.pack(pady=BOARD_PADDING)
        self.board_horizontal = ScrollRegion(
            self.board_scroll.body,
            self.skin,
            width=min(460, self._panel.content_width - 20),
            height=BOARD_HEIGHT,
            horizontal=True,
            autohide=True,
        )
        self.board_horizontal.frame.pack()
        self.board = tk.Canvas(
            self.board_horizontal.body,
            width=460,
            height=BOARD_HEIGHT,
            bg='#E6E1F2',
            highlightthickness=0,
        )
        self.board.pack()
        self.board.bind("<ButtonPress-1>", self._board_press)
        for source in (self.palette, self.board):
            source.bind("<B1-Motion>", self._drag.motion)
            source.bind("<ButtonRelease-1>", self._drag.release)
        self.board_horizontal.adopt()

    def greet(self) -> None:
        if self._sequence is not None:
            self._sequence.greet()

    def _fit_board(self, body_height: int | None = None) -> None:
        """Keep the palette and the entire board viewport inside the body."""
        if body_height is not None:
            self._cancel_layout()
        else:
            self._layout_timer = None
        if self._closed:
            return
        height = (
            self._panel.scroll.canvas.winfo_height()
            if body_height is None else body_height
        )
        if height <= 1:
            # Preserve the prepared pre-map budget until Tk allocates the body.
            return
        # winfo_y already includes the top padding; reserve only the bottom.
        available = height - self.board_scroll.frame.winfo_y() - BOARD_PADDING
        self.board_scroll.canvas.configure(
            height=max(1, min(BOARD_HEIGHT, available - 2)),
        )
        self._panel.scroll.canvas.yview_moveto(0)

    def _configured(self, event: tk.Event[tk.Misc]) -> None:
        if event.widget in (
            self.window, self._panel.scroll.canvas, self.board_scroll.frame,
        ):
            self._queue_layout()
        self._codes.move()

    def _queue_layout(self) -> None:
        if not self._closed and self._layout_timer is None:
            self._layout_timer = self.window.after_idle(self._fit_board)

    def _cancel_layout(self) -> None:
        if self._layout_timer is not None:
            self.window.after_cancel(self._layout_timer)
            self._layout_timer = None

    def _present(
        self,
        view: RoundView,
        score: SessionSummary,
        busy: bool,
        feedback_visible: int,
    ) -> None:
        self._view, self._busy, self._feedback_visible = view, busy, feedback_visible
        evaluated = feedback_visible == 4
        key = "game.player_win" if view.result == "win" else "game.aiko_win"
        status = (
            GERMAN_TEXT.format(key)
            if view.result is not None and evaluated
            else GERMAN_TEXT.format("mastermind.evaluating")
            if not evaluated
            else GERMAN_TEXT.format(
                "mastermind.remaining", remaining=str(ATTEMPTS - len(view.guesses))
            )
        )
        self._panel.update(
            score, status=status, finished=view.result is not None and not busy
        )
        enabled = self._editable()
        self.palette.configure(cursor="hand2" if enabled else "arrow")
        update_button_state(
            self.submit_button, enabled=enabled and not busy and None not in self._draft
        )
        update_button_state(self.clear_button, enabled=enabled and any(self._draft))
        self._draw_board()

    def _piece(self, canvas: tk.Canvas, color: str, x: int, y: int, tag: str) -> None:
        if color == "white":
            canvas.create_oval(
                x - 22, y - 22, x + 22, y + 22, fill="#B5C3D4", outline=self.skin.border
            )
        canvas.create_image(x, y, image=self._codes.images.get(color), tags=tag)

    def _draw_board(self) -> None:
        canvas = self.board
        canvas.delete("all")
        for x, key in (
            (40, "mastermind.board.guesses"),
            (232, "mastermind.board.feedback"),
        ):
            canvas.create_text(
                x,
                12,
                anchor="w",
                text=GERMAN_TEXT.format(key),
                fill=self.skin.muted,
                font=(self.skin.font, 9),
            )
        current = len(self._view.guesses)
        for row in range(ATTEMPTS):
            y = HEADER_HEIGHT + row * ROW_HEIGHT + 24
            active = row == current and self._view.result is None
            canvas.create_rectangle(
                2,
                y - 23,
                458,
                y + 23,
                outline='#C0A477' if active else '#AEA1C6',
                fill='#FFFAEF' if active else '#F3EDF7',
                width=2 if active else 1,
                tags="row",
            )
            canvas.create_text(14, y, text=str(row + 1), fill=self.skin.text)
            guess = self._view.guesses[row] if row < current else None
            colors = guess.colors if guess else self._draft if active else (None,) * 4
            for position, color in enumerate(colors):
                x = 52 + position * 48
                canvas.create_oval(
                    x - 21,
                    y - 21,
                    x + 21,
                    y + 21,
                    fill=self.skin.background,
                    tags="slot",
                    outline=self.skin.accent
                    if active and position == self._active
                    else self.skin.border,
                )
                if color:
                    self._piece(canvas, color, x, y, "guess" if guess else "draft")
                    canvas.create_text(
                        x + 16,
                        y + 15,
                        text=str(COLORS.index(color) + 1),
                        fill=self.skin.text,
                        font=(self.skin.font, 8, "bold"),
                    )
            visible = (
                (self._feedback_visible if row == current - 1 else 4) if guess else 0
            )
            exact = guess.feedback.exact if guess else 0
            misplaced = guess.feedback.misplaced if guess else 0
            for mark in range(4):
                x, cy = 235 + mark % 2 * 15, y - 8 + mark // 2 * 15
                fill = (
                    (
                        "#252A33"
                        if mark < exact
                        else "white"
                        if mark < exact + misplaced
                        else "#CBD3DD"
                    )
                    if mark < visible
                    else self.skin.background
                )
                canvas.create_oval(
                    x - 5,
                    cy - 5,
                    x + 5,
                    cy + 5,
                    fill=fill,
                    outline="#526175",
                    tags=("feedback", f"feedback{row}"),
                )
            if guess and visible == 4:
                canvas.create_text(
                    274,
                    y,
                    anchor="w",
                    fill=self.skin.text,
                    text=GERMAN_TEXT.format(
                        "mastermind.feedback",
                        exact=str(exact),
                        misplaced=str(misplaced),
                    ),
                    font=(self.skin.font, 9),
                )

    def _editable(self) -> bool:
        # Dialogue may run while the player prepares a guess. Evaluation and
        # terminal rounds still protect the board; submission has its own gate.
        return (not self._closed and self._feedback_visible == 4
                and self._view.result is None)

    def _palette_press(self, event: tk.Event[tk.Misc]) -> str:
        if self._editable():
            index = event.x // self._palette_step
            if 0 <= index < len(COLORS):
                return self._drag.begin(event, COLORS[index])
        return "break"

    def _slot_at(self, x_root: int, y_root: int) -> int | None:
        for viewport in (
            self.board_scroll.canvas,
            self.board_horizontal.canvas,
            self._panel.scroll.canvas,
        ):
            if not (
                viewport.winfo_rootx()
                <= x_root
                < viewport.winfo_rootx() + viewport.winfo_width()
                and viewport.winfo_rooty()
                <= y_root
                < viewport.winfo_rooty() + viewport.winfo_height()
            ):
                return None
        x, y = x_root - self.board.winfo_rootx(), y_root - self.board.winfo_rooty()
        row = (y - HEADER_HEIGHT) // ROW_HEIGHT
        if row != len(self._view.guesses) or not 28 <= x < 220:
            return None
        return (x - 28) // 48

    def _board_press(self, event: tk.Event[tk.Misc]) -> str:
        slot = self._slot_at(event.x_root, event.y_root)
        if self._editable() and slot is not None:
            self._active = slot
            self._draw_board()
            color = self._draft[slot]
            if color is not None:
                return self._drag.begin(event, color, slot)
            if self._selected_color is not None:
                self._draft[slot] = self._selected_color
                self._refresh()
        return "break"

    def _drop(self, color: str, source: int | None, x: int, y: int) -> None:
        target = self._slot_at(x, y)
        if self._editable() and target is not None:
            if source is not None:
                self._draft[source] = self._draft[target]
            self._draft[target] = color
            self._active = target
            self._refresh()

    def _refresh(self) -> None:
        assert self._sequence is not None
        self._sequence.interrupt_comment()
        self._present(
            self._view, self._sequence.game.score, self._busy, self._feedback_visible
        )

    def _click_piece(self, color: str, source: int | None) -> None:
        if not self._editable():
            return
        if self._sequence is not None:
            self._sequence.interrupt_comment()
        if source is not None:
            if self._selected_color is not None:
                self._draft[source] = self._selected_color
                self._refresh()
            return
        self._selected_color = color
        # Focus only after the completed click; keyboard reveal must not move
        # the palette while a pointer gesture is still in progress.
        self.palette.focus_set()
        self.palette.delete("selection")
        index = COLORS.index(color)
        self.palette.create_rectangle(
            index * self._palette_step + 1, 1,
            (index + 1) * self._palette_step - 1,
            38 if self._palette_step == 40 else 54,
            outline=self.skin.accent, width=2, tags="selection",
        )

    def choose(self, color: str) -> None:
        """Number keys fill the active slot; pointer input selects color then slot."""
        if self._editable() and color in COLORS:
            self._draft[self._active] = color
            self._active = (self._active + 1) % PLACES
            self._refresh()

    def clear_slot(self) -> None:
        if self._editable():
            self._draft[self._active] = None
            self._refresh()

    def _key_color(self, color: str, _event: tk.Event[tk.Misc]) -> None:
        self.choose(color)

    def _key_slot(self, delta: int, _event: tk.Event[tk.Misc]) -> None:
        if self._editable():
            self._active = (self._active + delta) % PLACES
            self._draw_board()

    def submit(self) -> None:
        if self._editable() and not self._busy and None not in self._draft:
            assert self._sequence is not None
            code = tuple(color for color in self._draft if color is not None)
            if self._sequence.submit(code):
                self._draft[:] = [None] * PLACES
                self._active = 0
                self._draw_board()
                row = min(len(self._view.guesses), ATTEMPTS - 1)
                top = HEADER_HEIGHT + row * ROW_HEIGHT
                viewport = self.board_scroll.canvas
                if top + ROW_HEIGHT > viewport.yview()[1] * BOARD_HEIGHT:
                    viewport.yview_moveto(
                        (top + ROW_HEIGHT - viewport.winfo_height()) / BOARD_HEIGHT
                    )

    def next_round(self) -> None:
        if not self._closed and self._sequence is not None:
            self._sequence.next_round()
            if not self._view.guesses:
                self.board_scroll.canvas.yview_moveto(0)

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)
        self._codes.set_topmost(enabled)
        if self._finale:
            self._finale.effects.set_topmost(enabled)

    def _look_feedback(self, row: int | None) -> None:
        if self._presentation is not None:
            self._presentation.look((
                self.board.winfo_rootx() + 312,
                self.board.winfo_rooty() + HEADER_HEIGHT + (row + .5) * ROW_HEIGHT,
            ) if row is not None else None)

    def close(self) -> None:
        if not self._closed and self._sequence is not None:
            self._closed = True
            self._drag.cancel()
            self._cancel_layout()
            if self._finale:
                self._finale.close()
            score = self._sequence.close()
            try:
                self._panel.destroy()
            finally:
                self._palette_images.clear()
                self._on_closed(score)
