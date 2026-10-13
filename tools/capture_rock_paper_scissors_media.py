"""Capture real Tk/Xvfb Rock–Paper–Scissors views for the PR media gallery.

These are development captures of the running application on Linux/Xvfb;
they must never be presented as native Windows screenshots. No synthetic
character or interface artwork is generated, and existing historical media
remains untouched. Pillow is needed only for this developer-only script.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

from PIL import Image, ImageGrab

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore


SCREENSHOT_BOX = (160, 180, 1260, 898)
MEDIA_DIR = Path(__file__).resolve().parents[1] / "vorschau"


def present(pet: DesktopPet) -> None:
    """Flush layout and the live X server between controlled game actions."""
    pet.root.update_idletasks()
    pet.root.update()
    time.sleep(0.08)


def capture(pet: DesktopPet) -> Image.Image:
    present(pet)
    image: Image.Image = ImageGrab.grab(bbox=SCREENSHOT_BOX).convert("RGB")
    if image.size != (1100, 718):
        raise RuntimeError("The desktop capture has unexpected dimensions")
    return image


def record_media() -> None:
    """Drive the actual game callbacks; capture one frame for every cue."""
    # Capture only the live sprite, player panel and Aiko's own bubble.
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aiko-media-") as folder:
        pet = DesktopPet(
            store=StateStore(Path(folder) / "preview-state.json"),
        )
        try:
            pet.settings.spontaneous_talk = False
            pet.settings.auto_routine = False
            pet.state.sleeping = False
            if pet._runtime.scheduled_greeting is not None:
                pet.root.after_cancel(pet._runtime.scheduled_greeting)
                pet._runtime.scheduled_greeting = None
            # Keep the sprite and interactive panel in the same live capture.
            pet._place_x(310)
            pet._on_enter()
            hover = pet._hover
            toolbar = hover.toolbar
            assert toolbar is not None
            toolbar.buttons["play"].invoke()
            game = hover.game_window
            assert game is not None
            hover.dismiss_outside(-999, -999)
            game.window.geometry("+620+335")
            present(pet)
            for window in (pet.root, game.window):
                if not window.winfo_ismapped():
                    raise RuntimeError("The actual game windows are not visible")
                print(
                    f"{window.winfo_name()}: "
                    f"({window.winfo_rootx()}, {window.winfo_rooty()}) "
                    f"{window.winfo_width()}x{window.winfo_height()}"
                )

            frames: list[Image.Image] = []
            durations: list[int] = []

            def frame(duration: int) -> None:
                frames.append(capture(pet))
                durations.append(duration)

            opening = capture(pet)
            opening.save(MEDIA_DIR / "Aiko_RPS_Start.png")
            frames.append(opening)
            durations.append(1500)

            # Show a deterministic first round: player wins with rock.
            game._sequence._game._random_index = lambda _size: 2
            game.choose(Move.ROCK)
            frame(800)  # Eins
            game._sequence.advance()
            frame(800)  # Zwei
            game._sequence.advance()
            frame(800)  # Drei
            game._sequence.advance()
            frame(700)  # Excitement emote
            game._sequence.advance()
            # Both independently owned hands are now fully visible.
            revealed = capture(pet)
            revealed.save(MEDIA_DIR / "Aiko_RPS_Aufgedeckt.png")
            frames.append(revealed)
            durations.append(2100)
            game._sequence.advance()
            frame(900)  # Defeat emote and the existing failed animation
            game._sequence.advance()
            frame(2300)  # Aiko's own defeat comment
            game._sequence.advance()
            frame(900)  # Input unlocked with one completed round

            # Demonstrate that scores are local and cumulative within a window.
            game._sequence._game._random_index = lambda _size: 1
            game.choose(Move.ROCK)
            for _ in range(4):
                game._sequence.advance()
            frame(1700)  # Aiko chooses paper; player window shows rock
            game._sequence.advance()
            frame(850)
            game._sequence.advance()
            frame(2400)
            game._sequence.advance()
            scoreboard = capture(pet)
            scoreboard.save(MEDIA_DIR / "Aiko_RPS_Punktestand.png")
            frames.append(scoreboard)
            durations.append(1700)

            frames[0].save(
                MEDIA_DIR / "Aiko_RPS_Spielablauf.gif",
                save_all=True,
                append_images=frames[1:],
                loop=0, duration=durations, disposal=2,
                optimize=True,
            )
            print(
                f"Captured {len(frames)} application frames, "
                f"{game.score.games} completed rounds"
            )
        finally:
            pet.quit()


if __name__ == "__main__":
    record_media()
