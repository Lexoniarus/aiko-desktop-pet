"""Shared Connect Four board; only Aiko's reactions appear on the desktop."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from functools import partial

from ...asset_paths import GAME_ART_DIR
from ...games.connect_four import COLUMNS, ROWS, Board, Move, landing_cell
from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...pet.content import GERMAN_TEXT
from ..common.scroll_region import ScrollRegion
from ..common.skin import AikoSkin
from ..common.window_geometry import BoundsAt
from ..view_models.connect_four_geometry import CELL, HEIGHT, MARGIN, PREVIEW, WIDTH
from .connect_four_sequence import ConnectFourSequence, Drop
from .connect_four_throw import ConnectFourThrow
from .game_panel import GamePanel
from .game_presentation import GamePresentation


class ConnectFourWindow:
    def __init__(
        self,
        root: tk.Tk,
        *,
        on_closed: Callable[[SessionSummary], None],
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
        self._closed = False
        self._on_closed = on_closed
        self._hover_column: int | None = None
        self._view = Board()
        self._busy = True
        self._drop: Drop | None = None
        self._sequence: ConnectFourSequence | None = None
        self._throw: ConnectFourThrow | None = None
        self._presentation = presentation
        self._focus_cell: int | None = None
        self.skin = skin
        self._panel = GamePanel(
            root,
            GERMAN_TEXT.format("game.name.connect_four"),
            close=self.close,
            next_round=self.next_round,
            skin=skin,
            always_on_top=always_on_top,
            game_id=GameId.CONNECT_FOUR,
            bounds_at=bounds_at,
            body_height=540,
        )
        self.window = self._panel.window
        self._tokens: dict[int, tk.PhotoImage] = {}
        self._legend_tokens: dict[int, tk.PhotoImage] = {}
        try:
            legend = tk.Frame(self._panel.body, bg=skin.background)
            legend.pack(anchor="w", pady=(0, 6))
            for player, color, label in ((1, "yellow", "player"), (2, "red", "aiko")):
                token = tk.PhotoImage(
                    master=root, file=str(GAME_ART_DIR / f"c4-{color}.png")
                ).subsample(3)
                self._tokens[player] = token
                self._legend_tokens[player] = token.subsample(2)
                tk.Label(
                    legend,
                    image=self._legend_tokens[player],
                    compound="left",
                    text=GERMAN_TEXT.format(f"connect_four.legend.{label}"),
                    bg=skin.background,
                    fg=skin.text,
                    font=(skin.font, 9),
                ).pack(side="left", padx=(0, 14))
            region = ScrollRegion(
                self._panel.body,
                skin,
                width=min(WIDTH, self._panel.content_width),
                height=HEIGHT,
                horizontal=True,
                autohide=True,
            )
            region.frame.pack()
            self.canvas = tk.Canvas(
                region.body,
                width=WIDTH,
                height=HEIGHT,
                bg=skin.background,
                highlightthickness=0,
                takefocus=True,
            )
            self.canvas.pack()
            self._board_face = tk.PhotoImage(
                master=root, file=str(GAME_ART_DIR / 'c4-board.png'),
            )
            if presentation is not None:
                self._throw = ConnectFourThrow(
                    self.window, self.canvas, presentation, topmost=always_on_top,
                )
            self.canvas.bind("<Motion>", self._hover)
            self.canvas.bind("<Leave>", self._leave)
            self.canvas.bind("<Button-1>", self._click)
            for column in range(COLUMNS):
                self.canvas.bind(
                    str(column + 1),
                    partial(self._key, column),
                )
            region.adopt()
            self._sequence = ConnectFourSequence(
                schedule=self.window.after,
                cancel=self.window.after_cancel,
                present=self._present,
                say=speak,
                animate=animate,
                emote=emote,
                dialogue=dialogue,
                round_event=round_event,
                express_event=express_event,
                throw=self._throw_move if self._throw else None,
                interrupt=interrupt, look=self._look_at,
            )
            self._present(
                self._sequence.game.board, self._sequence.game.score, True, None
            )
            self._panel.show(root)
            self.window.bind('<Configure>', lambda _: self._look_at(self._focus_cell),
                             add='+')
        except Exception:
            self._closed = True
            if self._throw:
                self._throw.close()
            if self._sequence is not None:
                self._sequence.close()
            self._panel.destroy()
            self._tokens.clear()
            self._legend_tokens.clear()
            raise

    def greet(self) -> None:
        if self._sequence is not None:
            self._sequence.greet()

    def _throw_move(self, move: Move, done: Callable[[], None]) -> None:
        if self._throw is not None:
            self._throw.play(move.cell, done)

    def _look_at(self, cell: int | None) -> None:
        self._focus_cell = cell
        if self._presentation is not None:
            self._presentation.look((
                self.canvas.winfo_rootx() + MARGIN + (cell % 7 + .5) * CELL,
                self.canvas.winfo_rooty() + PREVIEW + (cell // 7 + .5) * CELL,
            ) if cell is not None else None)

    def _present(
        self,
        board: Board,
        score: SessionSummary,
        busy: bool,
        drop: Drop | None,
    ) -> None:
        self._view, self._busy, self._drop = board, busy, drop
        self._draw()
        if board.winner is not None:
            key = {1: "game.player_win", 2: "game.aiko_win", 0: "game.draw"}[
                board.winner
            ]
        elif busy and board.turn == 1:
            key = "connect_four.wait"
        else:
            key = "game.player_turn" if board.turn == 1 else "game.aiko_turn"
        self._panel.update(
            score,
            status=GERMAN_TEXT.format(key),
            finished=board.winner is not None and not busy,
        )

    def _draw(self) -> None:
        canvas, board = self.canvas, self._view
        canvas.delete("all")
        for cell in range(ROWS * COLUMNS):
            x = MARGIN + (cell % COLUMNS + 0.5) * CELL
            y = PREVIEW + (cell // COLUMNS + 0.5) * CELL
            canvas.create_oval(
                x - 15.6,
                y - 15.6,
                x + 15.6,
                y + 15.6,
                fill="#FFFCFD",
                outline="#ABBACB",
                tags="hole",
            )
            if board.cells[cell] and (self._drop is None or cell != self._drop.cell):
                canvas.create_image(
                    x, y, image=self._tokens[board.cells[cell]], tags="piece"
                )
            if cell in board.winning_cells and self._drop is None:
                canvas.create_oval(
                    x - 18,
                    y - 18,
                    x + 18,
                    y + 18,
                    outline="#755C93",
                    width=4,
                    tags="winning",
                )
        if self._drop is not None and self._drop.fraction >= 0:
            drop = self._drop
            x = MARGIN + (drop.cell % COLUMNS + 0.5) * CELL
            target = PREVIEW + (drop.cell // COLUMNS + 0.5) * CELL
            y = 24 + (target - 24) * drop.fraction
            canvas.create_image(x, y, image=self._tokens[drop.player], tags="falling")
        canvas.create_image(0, 0, image=self._board_face,
                            anchor='nw', tags='board_face')
        canvas.tag_raise('winning')
        legal = not self._busy and board.winner is None and board.turn == 1
        column = self._hover_column
        valid = legal and column is not None and column in board.legal_columns
        canvas.configure(cursor="hand2" if valid else "arrow")
        if valid and column is not None:
            target_cell = landing_cell(board.cells, column)
            assert target_cell is not None
            x = MARGIN + (column + 0.5) * CELL
            y = PREVIEW + (target_cell // COLUMNS + 0.5) * CELL
            canvas.create_image(x, 24, image=self._tokens[1], tags="preview")
            canvas.create_oval(
                x - 16,
                y - 16,
                x + 16,
                y + 16,
                outline=self.skin.accent,
                width=3,
                dash=(4, 3),
                tags="preview",
            )

    def _column(self, x: int) -> int | None:
        column = (x - MARGIN) // CELL
        return column if 0 <= column < COLUMNS else None

    def _key(self, column: int, _event: tk.Event[tk.Misc]) -> None:
        self.choose(column)

    def _hover(self, event: tk.Event[tk.Misc]) -> None:
        self._hover_column = self._column(event.x)
        self._draw()

    def _leave(self, _event: tk.Event[tk.Misc]) -> None:
        self._hover_column = None
        self._draw()

    def _click(self, event: tk.Event[tk.Misc]) -> None:
        self.canvas.focus_set()
        column = self._column(event.x)
        if column is not None:
            self.choose(column)

    def choose(self, column: int) -> None:
        if not self._closed and self._sequence is not None:
            self._sequence.choose(column)

    def next_round(self) -> None:
        if not self._closed and self._sequence is not None:
            self._sequence.next_round()

    def set_topmost(self, enabled: bool) -> None:
        self.window.wm_attributes("-topmost", enabled)
        if self._throw:
            self._throw.effects.set_topmost(enabled)

    def close(self) -> None:
        if not self._closed and self._sequence is not None:
            self._closed = True
            if self._throw:
                self._throw.close()
            score = self._sequence.close()
            try:
                self._panel.destroy()
            finally:
                self._tokens.clear()
                self._legend_tokens.clear()
                self._on_closed(score)
