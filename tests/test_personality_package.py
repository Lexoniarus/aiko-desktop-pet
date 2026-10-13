"""Canonical personality modules and old public API share one implementation."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

from aiko_pet import adaptive, adaptive_models, adaptive_policy
from aiko_pet import computer_voice, dialogue, dialogue_catalog
from aiko_pet import dialogue_events, reaction_playback, reaction_sequence
from aiko_pet import work_episode
from aiko_pet.personality import (
    adaptive as canonical_adaptive,
    adaptive_models as canonical_models,
    adaptive_policy as canonical_policy,
    catalog, click_policy, mind, reaction_sequence as canonical_sequence,
    workload_events, work_episode as canonical_work,
)
from aiko_pet.presentation.reaction_playback import ReactionPlayer


ROOT = Path(__file__).resolve().parents[1] / "aiko_pet"


class PersonalityPackageTests(unittest.TestCase):
    def test_dialogue_types_share_one_canonical_owner(self) -> None:
        self.assertIs(dialogue.AikoMind, mind.AikoMind)
        self.assertEqual(mind.AikoMind.__module__, "aiko_pet.personality.mind")
        self.assertIs(dialogue.DialogueBook, catalog.DialogueBook)
        self.assertIs(dialogue.Reaction, catalog.Reaction)
        self.assertIs(dialogue_catalog.EMOTION_LABELS, catalog.EMOTION_LABELS)
        self.assertIs(dialogue_events.ClickDecision, click_policy.ClickDecision)
        self.assertIs(dialogue_events.choose_click_reaction,
                      click_policy.choose_click_reaction)

    def test_adaptive_objects_keep_exact_type_and_policy_identity(self) -> None:
        self.assertIs(adaptive.AdaptiveRoutine, canonical_adaptive.AdaptiveRoutine)
        self.assertIs(adaptive.Behaviour, canonical_models.Behaviour)
        self.assertIs(adaptive_models.Observation, canonical_models.Observation)
        self.assertIs(adaptive_models.AdaptiveMemory, canonical_models.AdaptiveMemory)
        self.assertIs(adaptive_policy.SleepOptions, canonical_policy.SleepOptions)

    def test_workload_detector_has_correct_name_and_legacy_aliases(self) -> None:
        detector = workload_events.WorkloadEventDetector
        self.assertIs(workload_events.ComputerVoice, detector)
        self.assertIs(computer_voice.ComputerVoice, detector)
        self.assertIs(dialogue.ComputerVoice, detector)
        self.assertEqual(detector.__module__,
                         "aiko_pet.personality.workload_events")

    def test_emote_and_playback_contracts_are_not_duplicated(self) -> None:
        self.assertIs(reaction_sequence.Cue, canonical_sequence.Cue)
        self.assertIs(reaction_sequence.compose_cues,
                      canonical_sequence.compose_cues)
        self.assertIs(reaction_playback.ReactionPlayer, ReactionPlayer)
        self.assertIs(work_episode.WorkEpisodeMemory, canonical_work.WorkEpisodeMemory)

    def test_dialogue_catalogue_path_still_points_to_original_data(self) -> None:
        self.assertEqual(
            catalog.CATALOGUE,
            ROOT / "data" / "dialogues.de.json",
        )
        self.assertTrue(catalog.CATALOGUE.is_file())
        book = catalog.DialogueBook.from_file()
        self.assertGreater(len(book.lines), 0)

    def test_old_flat_modules_do_not_own_more_implementations(self) -> None:
        old = (
            "adaptive.py", "adaptive_models.py", "adaptive_policy.py",
            "dialogue.py", "dialogue_catalog.py", "dialogue_events.py",
            "computer_voice.py", "work_episode.py", "reaction_sequence.py",
            "reaction_playback.py",
        )
        for name in old:
            with self.subTest(path=name):
                tree = ast.parse((ROOT / name).read_text("utf-8"))
                self.assertFalse(any(
                    isinstance(node, (ast.ClassDef, ast.FunctionDef))
                    for node in tree.body
                ))


if __name__ == "__main__":
    unittest.main()
