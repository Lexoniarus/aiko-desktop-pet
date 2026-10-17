"""Kenney-style coherent emote -> text -> emote reactions."""

import tempfile
import time
import tkinter as tk
import unittest
from pathlib import Path

from aiko_pet.asset_paths import EMOTE_IMAGE_DIR, KENNEY_UI_DIR
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.catalog import CATALOGUE, DialogueBook, Line, Reaction
from aiko_pet.pet.mind.reaction_sequence import EMOTES, Cue
from tools.pet_test_support import set_test_pet_values
from tools.pet_test_support import set_test_pet_values


class EmoteDomainTests(unittest.TestCase):
    def test_extracted_pixel_pngs_are_real_and_square(self):
        self.assertGreaterEqual(len(EMOTES), 12)
        for name in EMOTES:
            with self.subTest(name=name):
                p = EMOTE_IMAGE_DIR / f"emote_{name}.png"
                self.assertTrue(p.is_file())
                self.assertGreater(p.stat().st_size, 80)
                self.assertEqual(p.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_curated_catalogue_emotes_have_valid_names_and_inherit(self):
        lines = DialogueBook.from_file().lines
        emotes = [b.content for line in lines for b in line.beats if b.kind == "emote"]
        self.assertGreater(len(emotes), 150)
        self.assertTrue(all(name in EMOTES for name in emotes))

    def test_authored_beats_have_readable_text_and_deliberate_pauses(self):
        text = Cue.parse({"kind": "text", "content": "A" * 125})
        self.assertEqual(text.duration_ms, 7250)
        self.assertEqual(Cue.parse({"kind": "pause"}).duration_ms, 600)
        self.assertEqual(
            Cue.parse({"kind": "emote", "content": "heart"}).duration_ms, 800
        )

    def test_bad_emote_is_rejected_early(self):
        self.assertRaises(ValueError, Cue, "emote", "unsupported", 700)
        import json

        raw = json.loads(CATALOGUE.read_text(encoding="utf-8"))["lines"][0]
        raw["emote_before"] = "does-not-exist"
        self.assertRaises(ValueError, Line.parse, raw)

    def test_kenney_ui_pack_bitmaps_are_embedded(self):
        for name in (
            "button_regular.png",
            "button_wide.png",
            "button_small.png",
            "toolbar_banner.png",
        ):
            path = KENNEY_UI_DIR / name
            self.assertTrue(path.is_file())
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")


class EmoteTkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            root = tk.Tk()
        except tk.TclError as err:
            raise unittest.SkipTest("No screen for Tk tests") from err
        root.destroy()

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.pet = DesktopPet(store=StateStore(Path(temp.name) / "state.json"))
        self.addCleanup(self.pet.quit)
        if self.pet._runtime.scheduled_greeting:
            self.pet.root.after_cancel(self.pet._runtime.scheduled_greeting)
            self.pet._runtime.scheduled_greeting = None
        self.pet.settings.auto_routine = False
        set_test_pet_values(self.pet.state, sleeping=False)
        if self.pet._runtime.scheduled_tick is not None:
            self.pet.root.after_cancel(self.pet._runtime.scheduled_tick)
        self.pet._runtime.scheduled_tick = None

    def progress(self, milliseconds: int) -> None:
        time.sleep(milliseconds / 1000)
        self.pet.root.update()

    def is_emote(self) -> bool:
        if not self.pet._speech.bubble:
            return False
        first = self.pet._speech.bubble.winfo_children()[0]
        return isinstance(first, tk.Label) and bool(first.cget("image"))

    def bubble_text(self) -> str | None:
        if not self.pet._speech.bubble or self.is_emote():
            return None
        return (
            self.pet._speech.bubble.winfo_children()[0].winfo_children()[0].cget("text")
        )

    def test_three_beats_replace_each_other_and_never_overlap(self):
        reaction = Reaction(
            "test",
            (
                Cue("emote", "question", 700),
                Cue.text("...Oh."),
                Cue("emote", "heart", 900),
            ),
            "idle",
            "click_left",
        )
        self.pet._react(reaction, 1700)
        self.assertTrue(self.is_emote())
        self.assertEqual(len(self.pet._overlay_windows()), 2)
        self.progress(750)
        self.assertFalse(self.is_emote())
        self.assertEqual(self.bubble_text(), "...Oh.")
        self.assertEqual(len(self.pet._overlay_windows()), 2)
        self.progress(reaction.beats[1].duration_ms + 80)
        self.assertTrue(self.is_emote())
        self.assertEqual(len(self.pet._overlay_windows()), 2)
        self.progress(950)
        self.assertIsNone(self.pet._speech.bubble)

    def test_multiple_speech_lines_and_visual_after(self):
        reaction = Reaction(
            "test",
            (
                Cue("emote", "question", 700),
                Cue.text("Oh."),
                Cue.text("...Das hatte ich anders gemeint."),
                Cue("emote", "heart", 900),
            ),
            "waiting",
            "click_left",
        )
        self.pet._react(reaction, 1700)
        self.progress(750)
        self.assertEqual(self.bubble_text(), "Oh.")
        self.progress(reaction.beats[1].duration_ms + 80)
        self.assertEqual(self.bubble_text(), "...Das hatte ich anders gemeint.")
        self.progress(reaction.beats[2].duration_ms + 80)
        self.assertTrue(self.is_emote())

    def test_new_click_preempts_entire_older_reaction(self):
        reaction = Reaction(
            "test",
            (
                Cue("emote", "question", 700),
                Cue.text("Nicht mehr."),
                Cue.text("Alt und unerwünscht"),
                Cue("emote", "heart", 900),
            ),
            "waiting",
            "click_left",
        )
        self.pet._react(reaction, 1700)
        self.assertTrue(self.is_emote())
        self.pet._react(
            Reaction("new", (Cue.text("Jetzt hier."),), "idle", "click_right")
        )
        self.assertEqual(self.bubble_text(), "Jetzt hier.")
        self.progress(800)
        self.assertEqual(self.bubble_text(), "Jetzt hier.")
        self.assertIsNotNone(self.pet._reaction_player.pending_timer)

    def test_rapid_click_burst_does_not_stick_on_intro_emotes(self):
        reaction = Reaction(
            "rapid",
            (
                Cue("emote", "anger", 700),
                Cue.text("Ich höre dich."),
                Cue("emote", "cloud", 900),
            ),
            "idle",
            "rapid_click",
        )
        self.pet.mind.clicks.extend([1.0, 2.0, 3.0, 4.0])
        self.pet._contact.react_to_click(reaction)
        self.assertEqual(self.bubble_text(), "Ich höre dich.")

    def test_idle_emote_waits_until_dialogue_slot_is_free(self):
        self.pet._react(Reaction("x", (Cue.text("Ich rede."),), "idle", "click_left"))
        self.pet._attention_runtime.idle_emote()
        self.assertEqual(self.bubble_text(), "Ich rede.")
        self.pet._reaction_player.cancel()
        set_test_pet_values(self.pet.state, mood=3)
        self.pet._attention_runtime.idle_emote()
        self.assertTrue(self.is_emote())

    def test_hud_uses_kenney_assets_and_keeps_six_values(self):
        self.pet._on_enter()
        bar = self.pet._hover.toolbar
        assert bar is not None
        self.pet.root.update()
        self.assertTrue(bar.today.cget("image"))
        self.assertTrue(bar.buttons["feed"].cget("image"))
        self.assertEqual(len(bar.needs), 6)
        self.assertTrue(
            all(
                name in bar.buttons
                for name in (
                    "feed",
                    "play",
                    "pet",
                    "talk",
                    "sleep",
                )
            )
        )
        self.assertNotIn("energy_drink", bar.buttons)
        for key in bar.needs:
            set_test_pet_values(self.pet.state, **{key: 100})
        bar.refresh()
        self.pet.root.update()
        self.assertTrue(
            all(
                bar.needs[k][0].coords(bar.needs[k][1])[2]
                == bar.needs[k][0].winfo_width()
                for k in bar.needs
            )
        )


if __name__ == "__main__":
    unittest.main()
