"""Capture the current Aiko UI and sprite catalog for the public gallery.

All UI images come from the real Tk widgets under Linux/Xvfb. The animation
GIF uses the currently packaged runtime sprite PNGs and their timing manifest.
Historical images are retained in Git history rather than misidentified.
Pillow is a developer-only dependency, not an application runtime dependency.
"""

from __future__ import annotations

import json
import tempfile
import time
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageGrab

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.personality.catalog import Reaction

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / "vorschau"
CAPTURE_BOUNDS = (100, 130, 1260, 898)
STILLS = (
    "Aiko_Current_Hover.png",
    "Aiko_Current_Hover_Moved.png",
    "Aiko_Current_Dialog.png",
    "Aiko_Current_Reaction_Emote_Start.png",
    "Aiko_Current_Reaction_First_Line.png",
    "Aiko_Current_Reaction_Followup.png",
    "Aiko_Current_Reaction_Emote_End.png",
    "Aiko_Current_Status.png",
    "Aiko_Current_Settings.png",
    "Aiko_Current_Care_Pet.png",
    "Aiko_Current_Care_Feed.png",
    "Aiko_Current_Care_Sleep.png",
)
REACTION_GIF = "Aiko_Current_Reaction_Sequence.gif"
ANIMATION_GIF = "Aiko_Current_Animations.gif"


def settle(pet: DesktopPet) -> None:
    """Let Tk and the offscreen display map the actual application windows."""
    pet.root.update_idletasks()
    pet.root.update()
    time.sleep(0.07)


def live_capture(pet: DesktopPet, name: str) -> Image.Image:
    """Record real application pixels, not a re-created interface rendering."""
    if name not in STILLS:
        raise ValueError(f"Unknown gallery capture: {name}")
    settle(pet)
    if not pet.root.winfo_ismapped():
        raise RuntimeError("Aiko's actual desktop character is not visible")
    image: Image.Image = ImageGrab.grab(bbox=CAPTURE_BOUNDS).convert("RGB")
    if image.size != (1160, 768):
        raise RuntimeError("Unexpected gallery screenshot dimensions")
    background = Image.new("RGB", image.size, "#202733")
    if ImageChops.difference(image, background).getbbox() is None:
        raise RuntimeError("The screenshot contains only the empty desktop")
    image.save(PREVIEWS / name)
    print(f"Captured current UI: {name}")
    return image


def advance_reaction(pet: DesktopPet, index: int) -> None:
    """Advance the actual reaction player to a specific visible cue for media."""
    player = pet._reaction_player
    pending = player.pending_timer
    if pending is not None:
        pet.root.after_cancel(pending)
    player._advance(player.generation, index)


def capture_ui() -> None:
    """Capture each current care, window and multi-stage reaction surface."""
    with tempfile.TemporaryDirectory(prefix="aiko-current-gallery-") as folder:
        pet = DesktopPet(
            store=StateStore(Path(folder) / "media-preview-state.json"),
        )
        try:
            pet.settings.spontaneous_talk = False
            pet.settings.auto_walk = False
            pet.settings.auto_routine = False
            pet.settings.observe_computer = False
            pet.state.sleeping = False
            if pet._runtime.scheduled_greeting is not None:
                pet.root.after_cancel(pet._runtime.scheduled_greeting)
                pet._runtime.scheduled_greeting = None
            pet._place_x(610)
            pet._on_enter()
            hover = pet._hover
            bar = hover.toolbar
            if bar is None:
                raise RuntimeError("Could not open the actual care hover panel")
            settle(pet)

            pet._speech.show_text(
                "Hey! Schön, dass du da bist. Schau mal, wie es mir geht.",
                20000,
            )
            live_capture(pet, "Aiko_Current_Hover.png")

            # Use the panel's own dragging handlers; no fake panel rendering.
            drag_start = tk.Event()
            drag_start.x_root = bar.window.winfo_rootx() + 24
            drag_start.y_root = bar.window.winfo_rooty() + 12
            bar._drag_start(drag_start)
            drag_end = tk.Event()
            drag_end.x_root = drag_start.x_root - 140
            drag_end.y_root = drag_start.y_root - 40
            bar._drag_motion(drag_end)
            bar._drag_end(drag_end)
            live_capture(pet, "Aiko_Current_Hover_Moved.png")
            bar.reset_position()

            bar.hide()
            pet._speech.show_text(
                "Meine Sprechblase bleibt direkt bei mir, nicht beim Menü.",
                20000,
            )
            live_capture(pet, "Aiko_Current_Dialog.png")
            hover.show_toolbar()

            # The real ReactionPlayer drives the same speech/emote widgets as
            # production. Only its scheduled cue progression is controlled.
            reaction = Reaction(
                "gallery-reaction",
                "Hm? Hast du mich gerade gerufen?",
                "waving", "click_left",
                "Ach so! Ich bin ja schon da.",
                800, "question", "heart",
            )
            pet._react(reaction, 2500)
            reaction_frames = [
                live_capture(pet, "Aiko_Current_Reaction_Emote_Start.png"),
            ]
            advance_reaction(pet, 1)
            reaction_frames.append(live_capture(
                pet, "Aiko_Current_Reaction_First_Line.png",
            ))
            advance_reaction(pet, 2)
            reaction_frames.append(live_capture(
                pet, "Aiko_Current_Reaction_Followup.png",
            ))
            advance_reaction(pet, 3)
            reaction_frames.append(live_capture(
                pet, "Aiko_Current_Reaction_Emote_End.png",
            ))
            pet._reaction_player.cancel()
            reaction_frames[0].save(
                PREVIEWS / REACTION_GIF, save_all=True,
                append_images=reaction_frames[1:],
                duration=[800, 2400, 2250, 1150],
                loop=0, disposal=2, optimize=True,
            )
            print(f"Captured four real reaction cues: {REACTION_GIF}")

            pet._speech.hide()
            hover.show_toolbar()
            hover.open_status()
            if hover.status_panel is None:
                raise RuntimeError("The status view did not open")
            live_capture(pet, "Aiko_Current_Status.png")
            hover.status_panel.close()

            hover.show_toolbar()
            bar.settings_button.invoke()
            if hover.settings_popup is None:
                raise RuntimeError("The settings view did not open")
            live_capture(pet, "Aiko_Current_Settings.png")
            hover.settings_popup.close()

            hover.show_toolbar()
            pet.interact("pet")
            pet._speech.show_emote("heart", 9000)
            live_capture(pet, "Aiko_Current_Care_Pet.png")
            pet.interact("feed")
            live_capture(pet, "Aiko_Current_Care_Feed.png")
            pet.interact("sleep")
            live_capture(pet, "Aiko_Current_Care_Sleep.png")

            expected = {name for name in STILLS}
            missing = [name for name in expected if not (PREVIEWS / name).is_file()]
            if missing:
                raise RuntimeError(f"Missing current UI gallery captures: {missing}")
        finally:
            pet.quit()


def capture_current_sprite_animations() -> None:
    """Preview all 112 bundled runtime poses with real manifest durations."""
    manifest = json.loads(
        (ASSET_ROOT / "animations.json").read_text(encoding="utf-8"),
    )
    frames: list[Image.Image] = []
    durations: list[int] = []
    for clip in manifest["animations"]:
        state = str(clip["state"])
        for item in clip["frames"]:
            frame_file = ASSET_ROOT / str(item["file"])
            with Image.open(frame_file) as source:
                sprite = source.convert("RGBA")
            if sprite.size != (192, 208):
                raise RuntimeError(f"Unexpected sprite geometry: {frame_file}")
            preview = Image.new("RGBA", (224, 246), "#202733")
            preview.alpha_composite(sprite, (16, 30))
            ImageDraw.Draw(preview).text(
                (10, 8), state.replace("-", " "), fill="#b0e7fb",
            )
            frames.append(preview.convert("RGB"))
            durations.append(max(80, int(item["duration_ms"])))
    if len(frames) != 112:
        raise RuntimeError("Current Aiko asset catalog is not 112 poses")
    frames[0].save(
        PREVIEWS / ANIMATION_GIF,
        save_all=True, append_images=frames[1:],
        duration=durations, loop=0, disposal=2, optimize=True,
    )
    print(f"Captured {len(frames)} current sprite frames: {ANIMATION_GIF}")


def main() -> None:
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    capture_ui()
    capture_current_sprite_animations()


if __name__ == "__main__":
    main()
