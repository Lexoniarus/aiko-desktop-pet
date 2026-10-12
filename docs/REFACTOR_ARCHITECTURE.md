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
3. **Runtime orchestration (partially implemented):** `WalkController`,
   `FrameClock`, passive animation selection and the `ReactionPlayer`
   separate decisions/timing from Tk. `DesktopPet._tick()` is a named
   coordinator but the desktop shell is still larger than desired.
4. **Tk presentation (partially implemented):** `ui/speech_presenter.py`
   owns speech/emote windows and presentation timers without pet/domain
   imports. The existing GUI forwards its legacy speech APIs to it.
   The toolbar/status widgets still need narrower host interfaces.
5. **Pet and adaptive domain (implemented):** Care, friendship, bounded
   time progression and decay are separate policies. `adaptive_models.py`
   owns persisted memory/observation contracts, with `adaptive.py`
   orchestrating learning; legacy names and save-file fields remain valid.
6. **Dialogue (implemented):** Written dialogue catalogue, work-related
   comments, mouse-click decisions and spontaneous topics are independent
   of the GUI. The authored German text is untouched.
7. **Quality (continuous):** Ruff, PEP 8/E501, strict mypy across the
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
