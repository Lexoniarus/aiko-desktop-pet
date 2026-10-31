"""One cancellable timeline for guesses, code reveal and Aiko's reactions."""

from collections.abc import Callable
from uuid import uuid4

from ...games.contracts import GameId, GameRoundEvent, SessionSummary
from ...games.mastermind import Code, MastermindSession, RoundView
from ..common.game_pacing import GAME_PACING
from ..view_models.mastermind_models import CodeView
from .game_commentary import GameCommentary
from .rock_paper_scissors_dialogue import GameDialogue


class MastermindSequence:
    def __init__(
        self,
        *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None],
        present: Callable[[RoundView, SessionSummary, bool, int], None],
        show_code: Callable[[CodeView], None],
        hide_code: Callable[[], None],
        say: Callable[[str, int], None],
        animate: Callable[[str], None],
        emote: Callable[[str, int], None],
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _event: None,
        express_event: Callable[[str], None] = lambda _event: None,
        game: MastermindSession | None = None,
        finale: Callable[[bool, Callable[[], None]], None] | None = None,
        interrupt: Callable[[], None] = lambda: None,
        look: Callable[[int | None], None] = lambda _: None,
    ) -> None:
        self.game = game if game is not None else MastermindSession()
        self._schedule, self._cancel, self._present = schedule, cancel, present
        self._show_code, self._hide_code = show_code, hide_code
        self._say, self._animate, self._emote = say, animate, emote
        self._express_event = express_event
        self._dialogue = dialogue if dialogue is not None else GameDialogue().choose
        self._round_event, self._session_id = round_event, uuid4().hex
        self._closed = self._started = False
        self.busy = True
        self._feedback_visible = 4
        self._generation = 0
        self.pending_timer: str | None = None
        self._finale = finale
        self._interrupt, self._look = interrupt, look
        self._comments = GameCommentary(
            schedule=schedule, cancel=cancel, say=say, emote=emote,
            dialogue=self._dialogue, express=express_event,
        )

    def _show(self) -> None:
        self._present(
            self.game.view, self.game.score, self.busy, self._feedback_visible
        )

    def _later(self, delay: int, callback: Callable[[], None]) -> None:
        self._generation += 1
        if self.pending_timer is not None:
            self._cancel(self.pending_timer)
        generation = self._generation

        def run() -> None:
            if not self._closed and self._generation == generation:
                self.pending_timer = None
                callback()

        self.pending_timer = self._schedule(delay, run)

    def _react(
        self, event: str, *, emote: str | None = None, animation: str = "idle",
        then: Callable[[], None] | None = None,
    ) -> None:
        if event in ('game_mm_last', 'game_mm_progress'):
            self._comments.event(event, emote)
            self._ready()
            return
        self.busy = True
        self._show()
        self._animate(animation)
        text = self._dialogue(event)
        duration = GAME_PACING.text_ms(text)

        def speak() -> None:
            self._express_event(event)
            self._say(text, duration)
            self._later(duration, then or self._ready)

        if emote is None:
            speak()
        else:
            self._emote(emote, GAME_PACING.emote_ms)
            self._later(GAME_PACING.emote_ms, speak)

    def _begin(self) -> None:
        self._show_code(CodeView())
        self._round_event(
            GameRoundEvent(
                GameId.MASTERMIND, self._session_id, self.game.score.games + 1
            )
        )

    def greet(self) -> None:
        if not self._closed and not self._started:
            self._started = True
            self._begin()
            self._react("game_mm_greeting")

    def _ready(self) -> None:
        self.busy = False
        self._animate("idle")
        self._show()
        self._comments.later(1800, lambda: self._look(None))

    def submit(self, code: Code) -> bool:
        if self._closed or self.busy or self.game.view.result is not None:
            return False
        self.interrupt_comment()
        try:
            self.game.submit(code)
        except ValueError:
            return False
        self.busy = True
        self._feedback_visible = 0
        self._show()
        self._later(90, lambda: self._feedback(1))
        return True

    def _feedback(self, count: int) -> None:
        self._feedback_visible = count
        self._show()
        if count < 4:
            self._later(90, lambda: self._feedback(count + 1))
        else:
            self._after_feedback()

    def _after_feedback(self) -> None:
        self._look(len(self.game.view.guesses) - 1)
        if self.game.view.result is not None:
            # A fully evaluated guess counts even if code reveal is interrupted.
            self.game.settle()
            self._round_event(
                GameRoundEvent(
                    GameId.MASTERMIND,
                    self._session_id,
                    self.game.score.games,
                    self.game.view.result,
                )
            )
            self._show()
            self._later(180, lambda: self._reveal(1))
        elif len(self.game.view.guesses) == 9:
            self._react("game_mm_last")
        elif len(self.game.view.guesses) in (3, 6):
            self._react("game_mm_progress", emote="question")
        else:
            self._show()
            self._later(250, self._ready)

    def _reveal(self, count: int) -> None:
        self._show_code(CodeView(self.game.code_view(count)))
        if count < 4:
            self._later(180, lambda: self._reveal(count + 1))
        else:
            won = self.game.view.result == "win"
            if self._finale is not None:
                def begin() -> None:
                    if not self._closed and self._finale is not None:
                        self._finale(won, lambda: self._react('game_mm_snack_done')
                                     if not self._closed else None)
                self._react('game_mm_snack_win' if won else 'game_mm_spare_key',
                            emote='star' if won else 'drops', then=begin)
                return
            self._react(
                "game_mm_player_win" if won else "game_mm_aiko_win",
                emote="star" if won else "idea",
                animation="jumping" if won else "idle",
            )

    def next_round(self) -> None:
        if self._closed or self.busy or self.game.view.result is None:
            return
        self.game.next_round()
        self._comments.cancel()
        self.busy = True
        self._begin()
        self._react("game_mm_greeting")

    def close(self) -> SessionSummary:
        if not self._closed:
            self._closed = True
            self._comments.cancel()
            self._look(None)
            self._generation += 1
            if self.pending_timer is not None:
                self._cancel(self.pending_timer)
                self.pending_timer = None
            self.game.cancel()
            self._hide_code()
        return self.game.score

    def interrupt_comment(self) -> None:
        active = self._comments.active
        self._comments.cancel()
        if active:
            self._interrupt()
        self._look(None)
