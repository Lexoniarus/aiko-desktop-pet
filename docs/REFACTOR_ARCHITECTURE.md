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
   `application/activity.py` owns hardware observations, adaptive rhythm,
   and sleep-related decisions without Tk; GUI uses callback ports.
6. **Desktop composition (in progress):** `DesktopPet` in `gui.py`
   remains the compatibility façade and composition root, connecting
   independent animated character, utility UI, presentation and domain.
   This is **not** the animated character object. `gui.py` is still large
   (about 875 lines at this milestone), primarily because of bootstrap,
   callback adapters, legacy APIs and the main update loop. Split these
   further only through behavior-preserving, tested slices.
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
