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
   character, sprite frames, gaze, pointer observation and horizontal walking.
   Movement planning uses `WalkController`, animation timing uses
   `FrameClock`; comment timing and selection belong to
   `AttentionCoordinator`, not to the character UI.
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
   separate modules under `infrastructure/hardware/`;
   `system_activity.py` re-exports the old public names without
   housing another implementation.
6. **Desktop composition (in progress):** `DesktopPet` in `gui.py`
   assembles `AnimatedPet`, `DesktopWindow`, `HoverUi` and the application.
   `DesktopRuntime` receives explicit `DesktopTickPorts` rather than
   assuming a shell with inherited private phase methods. It still owns
   the original phase ordering and Tk tick/greeting timers.
   `desktop/preferences.py` now owns the cross-component consequences
   of setting toggles, scaling, centering and toolbar placement; the shell
   exposes short compatibility forwards.
   `desktop/input.py` owns Tk/global mouse input and its delayed focus
   timers, which `desktop/lifecycle.py` cancels before Tk teardown.
   `desktop/persistence.py` saves supplied state while
   `application/activity.py` advances pet time during ticks and saves.
   `desktop/maintenance.py` owns taskbar/stack intervals.
   The old façade `desktop/compatibility.py` is retained for historical
   callers but is no longer the runtime-stage provider. The composition
   shell is approximately 572 lines versus 875 before the audit.
   See [the full architecture audit](ARCHITECTURE_AUDIT_20261013.md).
7. **Pet and adaptive domain (implemented):** `PetState` now owns all
   care, needs, friendship and daily-routine state transitions.
   `care_actions.py`, `need_decay.py`, `friendship.py` and
   `pet_lifecycle.py` calculate immutable transitions or bounded
   simulation steps, without calling private methods on external records.
   Their existing module-level mutation APIs remain as legacy adapters to
   the aggregate or independent record adapters. `adaptive_models.py`
   owns persisted memory/observation contracts, with `adaptive.py`
   orchestrating learning; save fields and public names remain valid.
8. **Dialogue (implemented):** Written dialogue catalogue, mouse-click
   decisions and spontaneous topics are independent of the GUI.
   `work_episode.py` now owns the short-lived, observed work interruptions,
   session endings and one-time recovery follow-up. `AikoMind` coordinates
   event selection without duplicating work-episode memory. Authored
   German dialogue text is untouched.
9. **Quality (continuous):** Ruff, PEP 8/E501, strict mypy across the
   application, Pyright across application *and tests*, Python 3.11/3.13
   Linux/Xvfb GUI tests, and Windows-hosted headless checks are mandatory.
   The final interactive Windows smoke check remains outstanding.

## Session restoration and runtime settings

- `application/settings.py` owns the mutable `PetSettings` preference model.
  It is not part of JSON persistence. Its existing serialized fields and
  defaults remain unchanged; `storage.PetSettings` is a legacy type alias.
- `storage.StateStore.load_session()` decodes the complete saved state,
  preferences and adaptive memory in one read, returning `LoadedPetData`.
  The repository never calls `PetState.advance()`. The old `load()` and
  `load_memory()` entrypoints remain available for legacy consumers.
- `application/session.py` owns `PetSessionRestorer` and its
  `SavedPetReader` protocol. Only a valid existing version-one save receives
  the original bounded time advancement; a missing, corrupt or unsupported
  save starts fresh without an immediate simulation step.
- Application modules no longer import the concrete `storage` module.
  Persisted JSON schema version, save location, legacy defaults, assets and
  language policy do not change.

## Domain aggregate and transition decisions

- `PetState` is the one persisted mutable pet aggregate. Its `interact()`,
  `advance()` and `update_daily_routine()` methods own state updates.
- Immutable `CareTransition`, `NeedLevels`, `FriendshipTransition`,
  `RoutineTransition` and `SimulationStep` are calculated by separate
  stateless policy modules, without changing the input pet.
- Legacy `apply_care_action()`, `apply_need_decay()`,
  `award_friendship_for_care()`, `apply_daily_routine()` and
  `advance_pet_time()` remain available for existing consumers.
- The existing German `mood_hint()` and `feed_label()` methods remain
  compatibility APIs for now. Their presentation responsibilities should
  move with the read-model/projection boundary in the next architecture step,
  without creating a domain-to-UI import cycle.

## Application-read and presentation boundaries

- `application/read_snapshot.py` defines immutable `PetReadSnapshot`,
  carrying only needs, relationships and current state flags. Application
  consumers never require formatted German labels or Tk widget geometry.
- `telemetry.py` owns the immutable `ComputerSnapshot` value and effort
  calculation. Application coordinators use `application/ports.py`
  (`ComputerReadings` / `ComputerObservation`) instead of a concrete
  hardware provider; old `system_activity` imports keep the same class.
- `presentation/contracts.py` owns hover/status/settings view-model
  classes and `HoverAnchor`. The previous `application/view_models.py`
  path re-exports their exact types for backwards compatibility.
- The production desktop now uses `presentation/read_models.py` and
  `presentation/projections.py` to format German desktop copy. Pure
  `presentation/text_de.py` preserves all existing labels without
  making UI widgets depend on the mutable pet.
- Previous `application/hover_projection.py`,
  `application/status_projection.py` and `application/read_models.py`
  remain as legacy entrypoints for old callers and test compatibility.
  They are no longer wired into the main desktop UI. Remove them only
  after explicit import compatibility cutover.
- Settings commands use the typed `SettingKey` keys end-to-end.
  Unsupported names still raise `ValueError` in the desktop adapter.
- The original German `PetState` and `TimeContext` display methods are
  still available for existing callers, but production presenters no longer
  call them. The current `TimeContext.activity` and
  `TimeContext.next_activity` still contain existing German schedule labels.
  Those legacy schedule values can be separated in a later cutover.

## Desktop session and runtime phase ownership

- `DesktopTickPorts` declares named capabilities such as
  `advance_lifecycle`, `observe_pointer`, `render_character`,
  `refresh_hover` and `refresh_overlays_and_save`. The runtime
  never depends on `DesktopPet`, `DesktopCompatibility`, game state or Tk.
- `DesktopPreferences` coordinates already-owned settings effects without
  retaining another preference state. The desktop entrypoints `set_topmost`,
  `set_auto_walk`, `set_auto_routine`, `toggle_scale`, `center` and
  `reset_toolbar_position` remain available for legacy callers.
- `DesktopInput` tracks its own delayed FocusOut callback IDs.
  `DesktopLifecycle.stop()` cancels them before the Tk root is destroyed.
- The historical `DesktopCompatibility` façade still exists and the
  `DesktopPet` shell still inherits it for existing tests/consumers.
  That inheritance is not used by the active runtime, and final facade
  retirement needs a separate compatibility review.
- Internal domain state, German dialogue, sprite assets, settings keys,
  save JSON v1 and Tk phase ordering are unchanged.

## Change safety

- `main` is untouched until a reviewed merge.
- No asset regeneration, save-file migration or behavior change is part of the
  initial UI extraction.
- Tests: `python -m unittest discover -s tests -q` (use Xvfb on Linux).
- Review the full diff, rerun CI, and manually validate the taskbar/window
  behavior on Windows before merge.
