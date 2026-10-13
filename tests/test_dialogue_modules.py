"""Module boundary tests for the authored dialogue catalogue."""

from __future__ import annotations

import random
import unittest

from aiko_pet import dialogue
from aiko_pet.dialogue_catalog import (
    ANIMATIONS,
    CATALOGUE,
    EMOTION_LABELS,
    DialogueBook,
    Line,
    Reaction,
)
from aiko_pet.routine import context_at
from aiko_pet.work_episode import WorkEpisodeMemory


class DialogueModulesTests(unittest.TestCase):
    def test_legacy_imports_resolve_to_catalogue_types(self) -> None:
        self.assertIs(dialogue.Line, Line)
        self.assertIs(dialogue.Reaction, Reaction)
        self.assertIs(dialogue.DialogueBook, DialogueBook)
        self.assertIs(dialogue.ANIMATIONS, ANIMATIONS)
        self.assertIs(dialogue.CATALOGUE, CATALOGUE)
        self.assertIs(dialogue.EMOTION_LABELS, EMOTION_LABELS)

    def test_aiko_mind_owns_independent_work_episode_memory(self) -> None:
        mind = dialogue.AikoMind(rng=random.Random(12))
        self.assertIsInstance(mind.work, WorkEpisodeMemory)
        self.assertEqual(mind.work.interruptions, 0)

    def test_catalogue_is_still_available_without_gui(self) -> None:
        self.assertTrue(CATALOGUE.is_file())
        book = DialogueBook.from_file(rng=random.Random(12))
        self.assertGreater(len(book.lines), 150)
        self.assertTrue(all(line.animation in ANIMATIONS for line in book.lines))

    def test_selected_reaction_remains_same_public_type(self) -> None:
        line = Line(
            id="smoke", event="greeting", text="Hallo!",
            animation="idle", moods=(), periods=(), weekdays=(),
            weight=1, cooldown_seconds=0.0,
        )
        book = DialogueBook((line,), rng=random.Random(8))
        context = context_at(1760281200)
        result = book.choose("greeting", "calm", context, 100.0)
        self.assertIsInstance(result, dialogue.Reaction)
        assert result is not None
        self.assertEqual(result.text, "Hallo!")

    def test_line_parser_rejects_non_mapping_input(self) -> None:
        with self.assertRaises(ValueError):
            Line.parse(None)


if __name__ == "__main__":
    unittest.main()
