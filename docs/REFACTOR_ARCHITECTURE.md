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
   additional runtime scheduling can be extracted in later slices.
   Separate pure decisions from Tkinter side effects; introduce typed
   interfaces only where they make components replaceable and testable.
3. **Desktop presentation (in progress):** `ui/speech_presenter.py` now
   owns Tk speech/emote bubbles, cached icon assets and display timeouts.
   `DesktopPet` delegates drawing via compatibility methods; the view
   receives only a geometry provider and z-order callback, never PetState
   or the application router.
3. **Reaction playback (implemented):** `ReactionPlayer` now owns ordered
   emote/text cues, timer cancellation, generation guards and follow-up
   scheduling. The GUI injects Tk callbacks and remains responsible for actual
   rendering. Need-dependent idle emote choice is a pure function.
4. **Domain and dialogue (implemented):** `friendship.py` owns the daily
   cap, useful-care rewards and variety bonus. `care_actions.py` owns all
   six care actions behind a typed `CareState` interface. `need_decay.py`
   calculates established need-decay rates; `pet_lifecycle.py` applies
   local sleep/nap rules and bounded time catch-up. `value_rules.py`
   normalizes potentially malformed saved values. `PetState` keeps its
   existing public methods and serialized keys; no save-file migration.
   Authored German dialogue parsing and weighted rotation live in
   `dialogue_catalog.py`; `AikoMind` still decides when to speak.
   Hardware-effort event selection lives in `computer_voice.py` and
   `dialogue.py` continues re-exporting legacy public names.
5. **Infrastructure and quality (in progress):** Windows API, monitor access,
   and persistence are already in dedicated modules. Ruff linting runs over
   all Python source files, and E501 line-length checks cover the entire
   application plus tool modules. Strict Mypy checks cover the full
   application, and Pyright enforces typing across application, tools and
   tests. Windows manual smoke acceptance is tracked in
   docs/REFACTOR_ACCEPTANCE.md and is not yet completed.

## Change safety

- `main` is untouched until a reviewed merge.
- No asset regeneration, save-file migration or behavior change is part of the
  initial UI extraction.
- Tests: `python -m unittest discover -s tests -q` (use Xvfb on Linux).
- Review the full diff, rerun CI, and manually validate the taskbar/window
  behavior on Windows before merge.
