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

from aiko_pet.games.rock_paper_scissors import Move
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from tools.media_crop import CapturedFrame, capture_screen, save_sequence

MEDIA_DIR = Path(__file__).resolve().parents[1] / "vorschau"


def present(pet: DesktopPet) -> None:
    """Flush layout and the live X server between controlled game actions."""
    pet.root.update_idletasks()
    pet.root.update()
    time.sleep(0.08)


def capture(pet: DesktopPet) -> CapturedFrame:
    """Capture all visible Tk windows before applying per-view framing."""
    present(pet)
    return capture_screen(pet.root)


def assert_hand_fits(game: object) -> None:
    """Fail a capture if an actual hand is cropped or the slot changes size."""
    from aiko_pet.ui.windows.rock_paper_scissors_window import RockPaperScissorsWindow

    if not isinstance(game, RockPaperScissorsWindow):
        raise RuntimeError("Expected a Rock–Paper–Scissors window")
    game.window.update_idletasks()
    bounds = game.player_hand.bbox(game._hand_image_item)
    if bounds is None:
        raise RuntimeError("Selected hand is missing")
    left, top, right, bottom = bounds
    width, height = (
        game.player_hand.winfo_width(), game.player_hand.winfo_height(),
    )
    if not (
        left >= 0 and top >= 0 and right <= width and bottom <= height
        and right - left == 72 and bottom - top == 72
    ):
        raise RuntimeError(
            f"Hand image clipped: {bounds} in {width}x{height} canvas",
        )


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

            frames: list[CapturedFrame] = []
            durations: list[int] = []

            def frame(duration: int) -> None:
                frames.append(capture(pet))
                durations.append(duration)

            game.window.update_idletasks()
            expected_window = (
                game.window.winfo_width(), game.window.winfo_height(),
            )
            opening = capture(pet)
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
            assert_hand_fits(game)
            if (
                game.window.winfo_width(), game.window.winfo_height()
            ) != expected_window:
                raise RuntimeError("Minigame window shrank after the reveal")
            revealed = capture(pet)
            revealed.save_png(MEDIA_DIR / "Aiko_RPS_Aufgedeckt.png")
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
            assert_hand_fits(game)
            if (
                game.window.winfo_width(), game.window.winfo_height()
            ) != expected_window:
                raise RuntimeError("Minigame window shrank after second round")
            scoreboard = capture(pet)
            frames.append(scoreboard)
            durations.append(1700)

            save_sequence(
                frames, durations, MEDIA_DIR / "Aiko_RPS_Spielablauf.gif",
            )
            print(
                f"Captured {len(frames)} application frames, "
                f"{game.score.games} completed rounds"
            )
        finally:
            pet.quit()


if __name__ == "__main__":
    record_media()
