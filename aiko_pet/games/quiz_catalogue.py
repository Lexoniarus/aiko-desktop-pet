"""Validated immutable German quiz content; no networking or UI dependencies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Answer:
    id: str
    text: str


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    revision: int
    topic: str
    difficulty: str
    variety_group: str
    text: str
    answers: tuple[Answer, ...]
    correct_answer_id: str
    explanation: str


@dataclass(frozen=True, slots=True)
class QuizCatalogue:
    questions: tuple[Question, ...]

    @classmethod
    def load(cls, path: Path | None = None) -> QuizCatalogue:
        source = path or Path(__file__).resolve().parents[1] / "data/quiz.de.json"
        raw = json.loads(source.read_text(encoding="utf-8"))
        if (not isinstance(raw, dict) or type(raw.get("version")) is not int
                or raw["version"] != 1):
            raise ValueError("Unsupported quiz catalogue")
        rows = raw.get("questions")
        if not isinstance(rows, list) or len(rows) < 10:
            raise ValueError("Quiz needs at least ten approved questions")
        questions: list[Question] = []
        ids: set[str] = set()
        answer_ids: set[str] = set()
        prompts: set[str] = set()
        for row in rows:
            if not isinstance(row, dict) or row.get("editorial_status") != "approved":
                raise ValueError("Quiz contains unapproved content")
            fields = ("id", "topic", "difficulty", "variety_group", "question",
                      "correct_answer_id", "explanation")
            if any(not isinstance(row.get(k), str) or not row[k].strip()
                   for k in fields):
                raise ValueError("Missing quiz text")
            if (type(row.get("revision")) is not int or row["revision"] < 1
                    or row["difficulty"] not in ("easy", "medium", "tricky")
                    or row["id"] in ids or row["question"].casefold() in prompts):
                raise ValueError("Invalid or duplicate question")
            choices = row.get("answers")
            if not isinstance(choices, list) or len(choices) != 4:
                raise ValueError("Quiz needs four answers")
            answers: list[Answer] = []
            for choice in choices:
                if (not isinstance(choice, dict)
                        or any(not isinstance(choice.get(k), str)
                               or not choice[k].strip() for k in ("id", "text"))
                        or choice["id"] in answer_ids):
                    raise ValueError("Invalid or duplicate answer")
                answers.append(Answer(choice["id"], choice["text"]))
                answer_ids.add(choice["id"])
            if (len({a.text.casefold() for a in answers}) != 4
                    or row["correct_answer_id"] not in {a.id for a in answers}):
                raise ValueError("Ambiguous quiz choices")
            questions.append(Question(
                row["id"], row["revision"], row["topic"], row["difficulty"],
                row["variety_group"], row["question"], tuple(answers),
                row["correct_answer_id"], row["explanation"],
            ))
            ids.add(row["id"])
            prompts.add(row["question"].casefold())
        return cls(tuple(questions))
