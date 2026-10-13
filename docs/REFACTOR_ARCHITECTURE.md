# Modular OOP refactor — working architecture

Work branch: `refactor/oop-modular-architecture` (from `main` at `6c4d2cf1`).

## Goal and boundary

Make the Windows desktop companion easier to extend without changing its
animation timing, care mechanics, local dialogue, saved state, or window ordering.
The existing Python 3.11+ Tkinter runtime must remain usable without optional
third-party packages. Keep German runtime text and English documentation.

## Refactor stages

1. **UI separation (implemented):** `StatusPanel`, `ActionToolbar` and
   `SettingsPopup` live in `aiko_pet/ui/`; old imports remain compatible.
2. **Application commands and integration ingress (implemented):**
   `aiko_pet/application/` contains typed care/notification commands,
   the care use-case controller, owner-thread router and bounded inbox.
   Tk care buttons use this command route today. Future authenticated
   adapters can publish validated *data* without obtaining desktop internals.
   See [integration architecture](INTEGRATION_ARCHITECTURE.md).
3. **Animated pet (implemented):** `ui/animated_pet.py` owns the visible
   character, sprite frames, gaze, cursor attention and horizontal walking.
   Movement planning uses `WalkController`, animation timing uses
   `FrameClock`; the object has no `DesktopPet` or hover imports.
4. **Independent utility GUI (implemented):** `ui/hover_ui.py` owns the
   lifecycle of `ActionToolbar`, `StatusPanel` and `SettingsPopup`.
   Each window consumes immutable views and explicit action callbacks, not
   the whole `DesktopPet`. `application/read_models.py` projects local
   domain and monitor values into the view snapshots.
5. **Speech and activity presentation (implemented):**
   `ui/speech_presenter.py` owns speech/emote windows and hide timers.
   `application/activity.py` owns adaptive rhythm and sleep-related
   decisions without Tk; GUI uses callback ports. Sensor readings, native
   providers, NVIDIA CSV parsing and the background monitor are now
   separate hardware modules; `system_activity.py` re-exports the
   old public names without housing another implementation.
6. **Desktop composition (in progress):** `DesktopPet` in `gui.py`
   connects the actual animated character (`AnimatedPet`), native window
   (`DesktopWindow`), independent hover UI (`HoverUi`) and application core.
   `AttentionCoordinator` owns idle/spontaneous/notification timing.
   The old GUI-private methods now live as typed forwards in
   `desktop/compatibility.py`. `desktop/runtime.py` now owns the ordered
   update loop and timers; `desktop/persistence.py` owns serialization
   and autosave intervals; `desktop/maintenance.py` owns taskbar/stack
   polling; `desktop/input.py` owns Tk and global mouse input.
   `desktop/lifecycle.py` now owns the ordered startup/shutdown of
   already constructed desktop resources. The composition module is about
   569 lines rather than 608 (formerly 875).
   See [the full architecture audit](ARCHITECTURE_AUDIT_20261013.md).
7. **Pet and adaptive domain (implemented):** Care, friendship, bounded
   time progression and decay are separate policies. `adaptive_models.py`
   owns persisted memory/observation contracts, with `adaptive.py`
   orchestrating learning; legacy names and save-file fields remain valid.
8. **Dialogue (implemented):** Written dialogue catalogue, work-related
   comments, mouse-click decisions and spontaneous topics are independent
   of the GUI. The authored German text is untouched.
9. **Quality (continuous):** Ruff, PEP 8/E501, strict mypy across the
   application, Pyright across application *and tests*, Python 3.11/3.13
   Linux/Xvfb GUI tests, and Windows-hosted headless checks are mandatory.
   The final interactive Windows smoke check remains outstanding.

## Change safety

- `main` is untouched until a reviewed merge.
- No asset regeneration, save-file migration or behavior change is part of the
  initial UI extraction.
- Tests: `python -m unittest discover -s tests -q` (use Xvfb on Linux).
- Review the full diff, rerun CI, and manually validate the taskbar/window
  behavior on Windows before merge.
