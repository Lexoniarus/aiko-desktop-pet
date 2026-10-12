# Modular OOP refactor — working architecture

Work branch: `refactor/oop-modular-architecture` (from `main` at `6c4d2cf1`).

## Goal and boundary

Make the Windows desktop companion easier to extend without changing its
animation timing, care mechanics, local dialogue, saved state, or window ordering.
The existing Python 3.11+ Tkinter runtime must remain usable without optional
third-party packages. Keep German runtime text and English documentation.

## Refactor stages

1. **UI separation (first slice):** Move the three existing Tkinter widgets
   (`StatusPanel`, `ActionToolbar`, `SettingsPopup`) out of `gui.py` to
   `aiko_pet/ui/`. They keep their public names and can still be imported from
   `aiko_pet.gui` while callers migrate. Asset directories are defined once
   in `asset_paths.py`. This first step deliberately preserves access to the
   existing `DesktopPet` coordinator and its behavior.
2. **Application orchestration (in progress):** A headless `WalkController`,
   `FrameClock` and passive animation priority selector now own motion planning,
   sprite timing and visual decisions. The former `_tick()` now coordinates
   named lifecycle, taskbar, sprite, emote, dialogue and overlay update methods.
   `DesktopPet` still applies Tk geometry and interaction side effects. The
   remaining reaction/scheduling logic can be extracted in later slices.
   Separate pure decisions from Tkinter side effects; introduce typed
   interfaces only where they make components replaceable and testable.
3. **Reaction playback (implemented):** `ReactionPlayer` now owns ordered
   emote/text cues, timer cancellation, generation guards and follow-up
   scheduling. The GUI injects Tk callbacks and remains responsible for actual
   rendering. Need-dependent idle emote choice is a pure function.
4. **Domain and dialogue (in progress):** The authored German dialogue
   catalogue, validation, and weighted selection now live in
   `dialogue_catalog.py`, while `AikoMind` owns conversational decisions.
   `dialogue.py` preserves the original public imports. Split distinct rules
   for pet care, friendship,
   adaptive work/rest rhythms, and dialogue selection without changing state
   semantics. Preserve existing `state.json` schema and fallback behaviors.
5. **Infrastructure and quality:** Keep Windows API, monitor access, and
   persistence behind explicit boundaries; add focused linting, formatting,
   typing checks and regression tests after establishing a measured baseline.

## Change safety

- `main` is untouched until a reviewed merge.
- No asset regeneration, save-file migration or behavior change is part of the
  initial UI extraction.
- Tests: `python -m unittest discover -s tests -q` (use Xvfb on Linux).
- Review the full diff, rerun CI, and manually validate the taskbar/window
  behavior on Windows before merge.
