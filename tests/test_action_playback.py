"""Pet action playback timing belongs to the visual owner, not gui.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import Mock

from aiko_pet.pet.animation.character import (
    AnimationClip, AnimationFrame, CharacterCatalog,
)
from aiko_pet.ui.pet_view.action_playback import ActionPlayback


class ActionPlaybackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.begin = Mock()
        self.cancel = Mock()
        clips = {
            "idle": AnimationClip(
                "idle", (AnimationFrame(Path("idle.png"), 800),),
                True, (0, 0),
            ),
            "eat": AnimationClip(
                "eat", (AnimationFrame(Path("eat.png"), 2500),),
                False, (0, 0),
            ),
        }
        self.actions = ActionPlayback(
            CharacterCatalog(clips), begin=self.begin, cancel=self.cancel,
        )

    def test_non_loop_action_uses_authored_clip_duration(self) -> None:
        self.actions.start("eat", 0.0, started_at=100.0)
        self.assertEqual(self.actions.clip_id, "eat")
        self.assertEqual(self.actions.until, 102.5)
        self.begin.assert_called_once_with("eat", 100.0)

    def test_loop_action_uses_requested_duration(self) -> None:
        self.actions.start("idle", 3.0, started_at=200.0)
        self.assertEqual(self.actions.until, 203.0)

    def test_cancel_and_extend_keep_the_original_semantics(self) -> None:
        self.actions.start("eat", 0.0, started_at=100.0)
        self.actions.extend(104.0)
        self.actions.extend(103.0)
        self.assertEqual(self.actions.until, 104.0)
        self.actions.cancel_at(101.0)
        self.assertEqual(self.actions.until, 101.0)
        self.cancel.assert_called_once_with(101.0)
        self.assertEqual(self.actions.clip_id, "eat")


if __name__ == "__main__":
    unittest.main()
