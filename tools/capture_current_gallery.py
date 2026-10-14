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

from PIL import Image, ImageDraw

from tools.media_crop import CapturedFrame, capture_screen, save_sequence

from aiko_pet.asset_paths import ASSET_ROOT
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.pet.mind.catalog import Reaction

ROOT = Path(__file__).resolve().parents[1]
PREVIEWS = ROOT / "vorschau"
# Capture the complete Xvfb screen and derive a safe crop from mapped Tk
# window geometry; fixed rectangles used to clip the left side of the toolbar.
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
AMBIENT_GIF = "Aiko_Current_Ambient_Blink_And_Glance.gif"


def settle(pet: DesktopPet) -> None:
    """Let Tk and the offscreen display map the actual application windows."""
    pet.root.update_idletasks()
    pet.root.update()
    time.sleep(0.07)


def live_capture(pet: DesktopPet, name: str) -> CapturedFrame:
    """Save the real, fully visible Tk windows with a small even border."""
    if name not in STILLS:
        raise ValueError(f"Unknown gallery capture: {name}")
    settle(pet)
    frame = capture_screen(pet.root)
    frame.save_png(PREVIEWS / name)
    print(
        f"Captured {name} at {frame.cropped().width}×"
        f"{frame.cropped().height}, including all mapped windows"
    )
    return frame

def advance_reaction(pet: DesktopPet, index: int) -> None:
    """Advance the actual reaction player to a specific visible cue for media."""
    player = pet._reaction_player
    pending = player.pending_timer
    if pending is not None:
        pet.root.after_cancel(pending)
    player._advance(player.generation, index)


def capture_ambient_behavior(pet: DesktopPet) -> None:
    """Record one real Tk idle blink with resting gaps and a spontaneous gaze.

    Frame transitions are driven deterministically against the actual
    AnimatedPet and Canvas; GIF hold times represent the intended pacing.
    This is a test capture, not a wall-clock performance measurement.
    """
    # This is a temporary media-only state. Clear previous scripted care
    # deadlines so they cannot mask the passive idle director.
    pet.state.sleeping = False
    pet._action_until = 0.0
    pet._action_state = "idle"
    pet._reaction_player.cancel()
    pet._speech.hide()
    # Stop the normal tick: scripted capture timestamps must not be
    # overridden by a real-time desktop render between GIF frames.
    pet._runtime.stop()
    if pet._hover.toolbar is not None:
        pet._hover.toolbar.hide()
    pet.settings.auto_walk = False
    pet.settings.follow_cursor = False
    pet.settings.observe_computer = False
    now = time.monotonic()
    pet._animated.cancel_action(now)
    ambient = pet._animated._ambient
    ambient.next_blink_at = now + 200
    ambient.next_glance_at = now + 200
    pet._animated.render(now, 0, (0, 0))

    frames: list[CapturedFrame] = []
    durations: list[int] = []

    def add_frame(duration_ms: int) -> None:
        settle(pet)
        frames.append(capture_screen(pet.root))
        durations.append(duration_ms)

    # Capture the calmer one-pixel sway through the real Tk widget;
    # the feet and the selected gaze sprite remain anchored.
    for phase in range(8):
        pet._animated.render(now + phase * .42 + .01, 0, (0, 0))
        add_frame(420)
    ambient.next_blink_at = time.monotonic() - 1
    pet._animated.render(time.monotonic(), 0, (0, 0))
    if not ambient.blinking:
        raise RuntimeError("The real idle blink did not start")
    clip = pet._animated.assets.clips["idle"]
    add_frame(clip.timings[0])
    for _ in range(1, 8):
        at = pet._animated.frame_clock.frame_started_at
        pet._animated.show_frame("idle", at + clip.timings[0] / 1000 + .002)
        add_frame(clip.timings[0])
    at = pet._animated.frame_clock.frame_started_at
    pet._animated.show_frame("idle", at + clip.timings[-1] / 1000 + .002)
    if ambient.blinking or pet._animated.frame_clock.active_key != ("idle", 0):
        raise RuntimeError("Idle blink did not return to the neutral pose")
    # Resume slow motion after all eight blink frames, not during them.
    rest_at = ambient._motion_started_at
    for phase in range(8):
        pet._animated.render(rest_at + phase * .42 + .01, 0, (0, 0))
        add_frame(420)

    ambient.next_glance_at = time.monotonic() - 1
    ambient.next_blink_at = time.monotonic() + 200
    pet._animated.render(time.monotonic(), 0, (0, 0))
    if pet._animated.frame_clock.active_key is None:
        raise RuntimeError("Missing autonomous look")
    if pet._animated.frame_clock.active_key[0] != "look":
        raise RuntimeError("Autonomous look used the wrong sprite set")
    # Hold the same lateral look sprite while its head subtly rocks.
    look_at = time.monotonic()
    for phase in range(3):
        pet._animated.render(look_at + phase * .42, 0, (0, 0))
        add_frame(420)
        key = pet._animated.frame_clock.active_key
        if key is None or key[0] != "look":
            raise RuntimeError("Autonomous gaze ended before micro-motion")
    ambient.suspend(time.monotonic())
    back_at = time.monotonic()
    for phase in range(8):
        pet._animated.render(back_at + phase * .42 + .01, 0, (0, 0))
        add_frame(420)
    save_sequence(frames, durations, PREVIEWS / AMBIENT_GIF)
    print(
        f"Captured {len(frames)} real ambient UI frames: {AMBIENT_GIF}"
    )


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
            # Leave enough space for the entire left-anchored hover panel
            # instead of publishing a clipped toolbar at the screen edge.
            pet._place_x(850)
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
            bar._drag.start(drag_start)
            drag_end = tk.Event()
            drag_end.x_root = drag_start.x_root - 140
            drag_end.y_root = drag_start.y_root - 40
            bar._drag.move(drag_end)
            bar._drag.finish(drag_end)
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
            save_sequence(
                reaction_frames, [800, 2400, 2250, 1150],
                PREVIEWS / REACTION_GIF,
            )
            print(f"Captured four real reaction cues: {REACTION_GIF}")

            pet._speech.hide()
            hover.show_toolbar()
            hover.open_status()
            if bar.details is None:
                raise RuntimeError("The inline status details are missing")
            bar.toggle_details()
            live_capture(pet, "Aiko_Current_Status.png")
            bar.toggle_details()

            hover.show_toolbar()
            bar.settings_button.invoke()
            if hover.settings_window is None:
                raise RuntimeError("The settings view did not open")
            live_capture(pet, "Aiko_Current_Settings.png")
            hover.settings_window.close()

            hover.show_toolbar()
            pet.interact("pet")
            pet._speech.show_emote("heart", 9000)
            live_capture(pet, "Aiko_Current_Care_Pet.png")
            pet.interact("feed")
            live_capture(pet, "Aiko_Current_Care_Feed.png")
            pet.interact("sleep")
            live_capture(pet, "Aiko_Current_Care_Sleep.png")

            capture_ambient_behavior(pet)
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
