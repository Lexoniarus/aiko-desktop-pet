# Historical design record — modular OOP refactor

> This is the October 2026 refactor **work history**, retained for context.
> The work branch was merged through
> [PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2).
> For the authoritative current module layout see
> [ARCHITECTURE.md](ARCHITECTURE.md).

Original base commit: `6c4d2cf1`. Final refactor commit: `e5821f5`.
Merge commit on `main`: `073e7a4`.

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
   the whole `DesktopPet`. `presentation/read_models.py` converts semantic
   pet and monitor snapshots into desktop view models.
5. **Speech and activity presentation (implemented):**
   `ui/speech_presenter.py` owns speech/emote windows and hide timers.
   `application/activity.py` owns adaptive rhythm and sleep-related
   decisions without Tk; GUI uses callback ports. Sensor readings, native
   providers, NVIDIA CSV parsing and the background monitor are now
   separate modules under `infrastructure/hardware/`;
   `system_activity.py` re-exports the old public names without
   housing another implementation.
6. **Desktop composition (implemented, legacy façade retained):** `DesktopPet`
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
7. **Pet and adaptive domain (implemented):** The real `PetState` owner,
   immutable care/need/friendship transitions, daily routine and bounded
   time progression now live together under `aiko_pet/pet/`.
   The original flat imports are explicit legacy aliases, not duplicate
   implementations. Stateless rules never mutate private aggregate state.
   Their existing module-level mutation APIs remain as legacy adapters to
   the aggregate or independent record adapters. `adaptive_models.py`
   owns persisted memory/observation contracts, with `adaptive.py`
   orchestrating learning; save fields and public names remain valid.
8. **Personality (implemented):** `aiko_pet/personality/` owns the
   adaptive observation/learning models, dialogue catalogue, `AikoMind`,
   click policy, work-episode memory and the event-only
   `WorkloadEventDetector`. The misleading legacy name `ComputerVoice`
   is still a type-identical alias. `personality/reaction_sequence.py`
   describes validated dialogue cues, while the actual playback belongs
   to `presentation/reaction_playback.py`. Authored German text and
   reaction sequence timing are unchanged.
9. **Quality (continuous):** Ruff, PEP 8/E501, strict mypy across the
   application, Pyright across application *and tests*, Python 3.11/3.13
   Linux/Xvfb GUI tests, and Windows-hosted headless checks are mandatory.
   Native Windows operation was reported successful by the user on
   2026-10-13; there is no independent item-by-item test log.

## Session restoration and runtime settings

- `application/settings.py` owns the mutable `PetSettings` preference model.
  It is not part of JSON persistence. Its existing serialized fields and
  defaults remain unchanged; `storage.PetSettings` is a legacy type alias.
- `infrastructure.persistence.StateStore.load_session()` decodes saved state,
  preferences and adaptive memory in one read, returning `LoadedPetData`.
  The repository never calls `PetState.advance()`. The old `load()` and
  `load_memory()` entrypoints remain available for legacy consumers.
  `storage.py` re-exports the exact canonical repository class.
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
- The previous `application/hover_projection.py`,
  `application/status_projection.py`,
  `application/settings_projection.py` and
  `application/read_models.py` are import-only legacy entrypoints.
  Their canonical implementation is `presentation/legacy.py`,
  preserving historical signatures and public view-source references.
  Only `presentation/` formats the actual desktop display models.
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

## Package migration: canonical pet context

- `pet/state.py` owns the only `PetState`. Its care/needs/friendship
  rules, routine/time planning and validations live alongside it.
- Old imports (`domain`, `care_actions`, `friendship`,
  `need_decay`, `pet_lifecycle`, `routine`, `value_rules`)
  now re-export the **identical** classes and functions for prior users.
- Runtime consumers reference the canonical pet context directly.
  There are no additional persisted objects, schemas or backfilled
  history. This is a package migration, not a simulation change.
- Further personality/desktop ownership moves happen as separate,
  testable packages after this pet cutover.

## Personality package and naming cutover

- All adaptive state, dialogue selection, work-episode and workload-event
  implementations live in `personality/`; legacy flat files re-export
  these exact objects without duplicate state or rules.
- `WorkloadEventDetector` is the accurate English class name. The
  historical `ComputerVoice` import and `DesktopPet.computer_voice`
  attribute still refer to the exact same detector.
- `presentation/reaction_playback.py` owns playback, whereas
  `personality/reaction_sequence.py` owns validated reaction cue data.
  Old imports remain supported.
- The authored JSON dialogue catalogue retains its exact path under
  `aiko_pet/data/`. No new model, audio generator, listener or API
  is introduced.

## Native desktop and visual-policy package cutover

- `desktop/geometry.py` owns the `TaskbarTrack` dataclass and taskbar
  foot baseline, without Win32 or Tk calls.
- `desktop/taskbar.py`, `desktop/window_stack.py` and
  `desktop/global_input.py` own native Windows discovery, foreground
  stacking and read-only global click/idle observation respectively.
- `presentation/animation.py`, `presentation/gaze.py` and
  `presentation/movement.py` own pure sprite timing and motion rules.
  Presentation's movement planner depends only on pure desktop geometry,
  never on native API access.
- All six former root modules remain re-export compatibility shims.
  Legacy patches to the shared standard-library `random`, `time`,
  `sys` and `ctypes` modules still address those exact shared modules.

## Canonical persistence infrastructure

- `infrastructure/persistence.py` now owns versioned, atomic local JSON
  storage and save-path resolution. `storage.py` is only a compatibility
  re-export, so no second repository implementation exists.
- Relative `AIKO_SAVE_PATH` overrides still resolve from the repository
  root despite the module's deeper location. The Windows LOCALAPPDATA
  default and XDG alternatives are unchanged.
- `PetSessionRestorer` still applies existing-save catch-up in the
  application. No startup policy moved back into infrastructure.

## Final dependency review and legacy transition

- New static tests cover import cycles and package boundaries. The legacy
  application view paths are import-only re-exports rather than duplicate
  text/geometry implementations.
- The old `DesktopViewSource` class is a `DesktopPresentation` subclass
  retaining its constructor and public component references. The active
  desktop and lifecycle import their hardware monitor canonically.
- `DesktopCompatibility` remains for existing callers; it does not
  participate in the runtime tick contract. Its final removal would require
  a separately approved breaking compatibility change.
- `ActionToolbar` construction, need bars, dragging and window visibility
  remain cohesive; splitting by line count alone is not justified.
- Localized domain convenience methods on `PetState` and `TimeContext`
  remain legacy APIs. Only `presentation/text_de.py` generates the
  production status and hover copy.
- The user confirmed native Windows operation on 2026-10-13. The final
  cleanup changes legacy access, imports and checks, not Tk rendering.

## Change safety

- During the refactor, `main` was untouched until the reviewed PR #2 merge.
- No asset regeneration, save-file migration or behavior change is part of the
  initial UI extraction.
- Tests: `python -m unittest discover -s tests -q` (use Xvfb on Linux).
- The final diff and CI were reviewed and the maintainer reported successful
  Windows operation before the approved merge. These were historical gates.
