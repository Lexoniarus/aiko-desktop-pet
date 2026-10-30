"""Quizmaster-led release, answer presentation and visible resolution boundary."""
from __future__ import annotations

import textwrap
from collections.abc import Callable
from uuid import uuid4

from ...games.contracts import GameId, GameRoundEvent
from ...games.quiz import QuizSession
from ..common.game_pacing import GAME_PACING
from .rock_paper_scissors_dialogue import GameDialogue


class QuizSequence:
    def __init__(
        self, game: QuizSession, *,
        schedule: Callable[[int, Callable[[], None]], str],
        cancel: Callable[[str], None], present: Callable[[], None],
        say: Callable[[str, int], None], animate: Callable[[str], None],
        emote: Callable[[str, int], None],
        dialogue: Callable[[str], str] | None = None,
        round_event: Callable[[GameRoundEvent], None] = lambda _: None,
        express_event: Callable[[str], None] = lambda _: None,
        look: Callable[[int | None], None] = lambda _: None,
    ) -> None:
        self.game = game
        self._schedule, self._cancel, self._present = schedule, cancel, present
        self._say, self._animate, self._emote = say, animate, emote
        self._express_event, self._look = express_event, look
        self._dialogue = dialogue or GameDialogue().choose
        self._event, self._session = round_event, uuid4().hex
        self._closed = self._started = self._round_started = False
        self.busy = True
        self.revealed = self.question_visible = False
        self.visible_answers = self.visible_correct = 0
        self._timer: str | None = None
        self._generation = self._wait_count = 0

    def _later(self, ms: int, action: Callable[[], None]) -> None:
        generation = self._generation

        def run() -> None:
            self._timer = None
            if not self._closed and generation == self._generation:
                action()
        self._timer = self._schedule(ms, run)

    def _read(self, text: str, done: Callable[[], None]) -> None:
        chunks = textwrap.wrap(text, width=120, break_long_words=False,
                               break_on_hyphens=False) or ["…"]

        def part(index: int) -> None:
            # Catalogue text remains complete, split into readable bubble occupants.
            if index == len(chunks):
                done()
                return
            duration = GAME_PACING.text_ms(chunks[index])
            self._say(chunks[index], duration)
            self._later(duration, lambda: part(index + 1))
        part(0)

    def _line(self, event: str, done: Callable[[], None]) -> None:
        self._express_event(event)
        self._read(self._dialogue(event), done)

    def _ready(self) -> None:
        if not self._closed:
            self.busy = False
            self._look(None)
            self._animate("idle")
            self._present()

    def _begin(self) -> None:
        self._round_started = True
        self._event(GameRoundEvent(
            GameId.QUIZ, self._session, self.game.rounds_completed + 1,
        ))
        self._line('game_quiz_greeting', self._question)

    def greet(self) -> None:
        if not self._closed and not self._started:
            self._started = True
            self._begin()

    def _question(self) -> None:
        self.busy = True
        self.revealed = False
        self.visible_answers = 0
        self.question_visible = True
        self._look(-1)
        self._present()
        self._read(self.game.current.text, lambda: self._answer_intro(0))

    def _answer_intro(self, index: int) -> None:
        if index == 4:
            self._look(None)
            self._line('game_quiz_release', self._ready)
            return
        self.visible_answers = index + 1
        self._look(index)
        self._present()
        text = f"{chr(65 + index)}: {self.game.current.answers[index].text}"
        self._read(text, lambda: self._answer_intro(index + 1))

    def answer(self, answer_id: str) -> bool:
        if self._closed or self.busy or not self._round_started:
            return False
        try:
            self.game.answer(answer_id)
        except ValueError:
            return False
        self._generation += 1
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
        self.busy = True
        self._look(None)
        self._present()  # Selection only; correctness and score remain concealed.
        self._line('game_quiz_lock', lambda: self._later(250, self._resolve))
        return True

    def _resolve(self) -> None:
        self.revealed = True
        self.visible_correct = self.game.correct
        self._present()
        if self._closed:
            return
        if self.game.finished:
            self._event(GameRoundEvent(
                GameId.QUIZ, self._session, self.game.rounds_completed, 'completed',
            ))
        right = self.game.selected == self.game.current.correct_answer_id
        event = 'game_quiz_correct' if right else 'game_quiz_incorrect'
        if self.game.error_streak >= 2:
            event = 'game_quiz_encourage'
        self._emote('star' if right else 'cloud', GAME_PACING.emote_ms)
        self._later(GAME_PACING.emote_ms, lambda: self._line(event, self._explain))

    def _explain(self) -> None:
        def aside() -> None:
            self._line('game_quiz_meta', lambda: self._line(
                'game_quiz_finish', self._ready,
            ) if self.game.finished else self._ready())
        self._read(self.game.current.explanation, aside)

    def wait_comment(self) -> None:
        if not self._closed and not self.busy and self.game.selected is None:
            # One short hint-free reminder; a decision interrupts it in the same owner.
            self._wait_count += 1
            if self._wait_count % 2:
                text = self._dialogue('game_quiz_wait')
                self._say(text, GAME_PACING.text_ms(text))
            else:
                self._read(self.game.current.text, lambda: None)

    def advance(self) -> None:
        if self._closed or self.busy or not self.revealed:
            return
        self.busy = True
        self.question_visible = self.revealed = False
        self.visible_answers = 0
        if self.game.finished:
            self.game.new_round()
            self.visible_correct = 0
            self._present()
            self._begin()
        else:
            self.game.advance()
            self._question()

    def close(self) -> None:
        self._closed = True
        self._generation += 1
        self._look(None)
        if self._timer is not None:
            self._cancel(self._timer)
            self._timer = None
