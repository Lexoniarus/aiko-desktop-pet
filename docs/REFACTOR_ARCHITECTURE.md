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
2. **Application orchestration:** Extract frame selection, walking decisions,
   reactions, and scheduling from the monolithic `DesktopPet` class.
   Separate pure decisions from Tkinter side effects; introduce typed
   interfaces only where they make components replaceable and testable.
3. **Domain and dialogue:** Split distinct rules for pet care, friendship,
   adaptive work/rest rhythms, and dialogue selection without changing state
   semantics. Preserve existing `state.json` schema and fallback behaviors.
4. **Infrastructure and quality:** Keep Windows API, monitor access, and
   persistence behind explicit boundaries; add focused linting, formatting,
   typing checks and regression tests after establishing a measured baseline.

## Change safety

- `main` is untouched until a reviewed merge.
- No asset regeneration, save-file migration or behavior change is part of the
  initial UI extraction.
- Tests: `python -m unittest discover -s tests -q` (use Xvfb on Linux).
- Review the full diff, rerun CI, and manually validate the taskbar/window
  behavior on Windows before merge.
