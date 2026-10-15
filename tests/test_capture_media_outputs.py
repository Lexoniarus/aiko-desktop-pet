"""Manual media tools must not recreate discarded standalone detail images."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from tools import capture_current_gallery as gallery
from tools import capture_rock_paper_scissors_media as rps
from tools.media_crop import CapturedFrame


class CaptureMediaOutputTests(unittest.TestCase):
    def test_manual_tools_write_only_the_six_public_media(self) -> None:
        pet = MagicMock()
        pet._runtime.scheduled_greeting = None
        pet._reaction_player.pending_timer = None
        game = pet._hover.game_window
        for window in (pet.root, game.window):
            window.winfo_width.return_value = 900
            window.winfo_height.return_value = 550
            window.winfo_rootx.return_value = 0
            window.winfo_rooty.return_value = 0
            window.winfo_name.return_value = "media-test"
            window.winfo_ismapped.return_value = True
        game.score.games = 2
        frame = CapturedFrame(
            Image.new("RGB", (160, 160), "white"), ((30, 30, 100, 100),),
        )
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)

            def record_ambient(_pet: object) -> None:
                # Ambient playback has its own behavioral regressions. Exercise
                # the unchanged encoder without a real desktop screenshot here.
                gallery.save_sequence([frame], [420], output / gallery.AMBIENT_GIF)

            with (
                patch.object(gallery, "PREVIEWS", output),
                patch.object(gallery, "DesktopPet", return_value=pet),
                patch.object(gallery, "settle"),
                patch.object(gallery, "capture_screen", return_value=frame),
                patch.object(gallery, "capture_ambient_behavior", record_ambient),
                patch.object(rps, "MEDIA_DIR", output),
                patch.object(rps, "DesktopPet", return_value=pet),
                patch.object(rps, "present"),
                patch.object(rps, "capture_screen", return_value=frame),
                patch.object(rps, "assert_hand_fits"),
                patch("builtins.print"),
            ):
                gallery.main()
                rps.record_media()
            self.assertEqual({path.name for path in output.iterdir()}, {
                "Aiko_Current_Hover.png",
                "Aiko_Current_Reaction_Sequence.gif",
                "Aiko_Current_Ambient_Blink_And_Glance.gif",
                "Aiko_Current_Animations.gif",
                "Aiko_RPS_Aufgedeckt.png",
                "Aiko_RPS_Spielablauf.gif",
            })
            self.assertTrue(all(path.stat().st_size for path in output.iterdir()))
        self.assertEqual(pet.quit.call_count, 2)


if __name__ == "__main__":
    unittest.main()
