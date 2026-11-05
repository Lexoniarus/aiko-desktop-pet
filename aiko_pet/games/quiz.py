"""A ten-question shared quiz, with stable answer identity and no time limit."""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import replace

from .quiz_catalogue import Question, QuizCatalogue

QUESTIONS_PER_ROUND = 10


class QuizSession:
    def __init__(
        self, catalogue: QuizCatalogue, rng: random.Random | None = None,
    ) -> None:
        if len(catalogue.questions) < QUESTIONS_PER_ROUND:
            raise ValueError("Quiz needs ten distinct questions")
        self.catalogue = catalogue
        self.rng = rng or random.Random()
        self.recent: set[str] = set()
        self.rounds_completed = 0
        self.questions: tuple[Question, ...] = ()
        self.index = self.correct = self.error_streak = 0
        self.selected: str | None = None
        self.finished = False
        self.new_round()

    @property
    def current(self) -> Question:
        return self.questions[self.index]

    def new_round(self) -> None:
        if self.questions and not self.finished:
            raise ValueError("Current quiz is not complete")
        pool = list(self.catalogue.questions)
        self.rng.shuffle(pool)
        chosen: list[Question] = []
        topics: Counter[str] = Counter()
        weights = Counter(q.topic for q in pool)
        groups: Counter[str] = Counter()
        for _ in range(QUESTIONS_PER_ROUND):
            # Prefer new topics/works and unasked questions, without rigid quotas.
            question = min(pool, key=lambda q: (
                q.id in self.recent, groups[q.variety_group],
                topics[q.topic] / weights[q.topic],
            ))
            pool.remove(question)
            choices = list(question.answers)
            self.rng.shuffle(choices)
            chosen.append(replace(question, answers=tuple(choices)))
            topics[question.topic] += 1
            groups[question.variety_group] += 1
        self.questions = tuple(chosen)
        self.index = self.correct = self.error_streak = 0
        self.selected = None
        self.finished = False

    def answer(self, answer_id: str) -> bool:
        if self.selected is not None or self.finished:
            raise ValueError("Question already answered")
        if answer_id not in {a.id for a in self.current.answers}:
            raise ValueError("Answer does not belong to current question")
        self.selected = answer_id
        self.recent.add(self.current.id)
        right = answer_id == self.current.correct_answer_id
        self.correct += int(right)
        self.error_streak = 0 if right else self.error_streak + 1
        if self.index == QUESTIONS_PER_ROUND - 1:
            self.finished = True
            self.rounds_completed += 1
        return right

    def advance(self) -> None:
        if self.selected is None or self.finished:
            raise ValueError("No next question")
        self.index += 1
        self.selected = None
