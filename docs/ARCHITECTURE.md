# Architecture — current `main`

Aiko Desktop Pet is a local-first Windows companion built with Python 3.11+, Tkinter and prepared PNG artwork. The program requires no remote services or inference model at runtime. This document describes the **current code structure**, not the original v0.7–v0.13 implementation history.

The key design principle: **one owner per mutable state or external side effect**, with small, named interfaces between components. Imports point directly to the packages that own each responsibility.

## Dependency overview

```mermaid
flowchart TB
    Shell["gui.py — DesktopPet (composition root)"]
    App["application/ — care, attention, activity, read models"]
    Domain["pet/ — PetState and pure policy transitions"]
    Mind["personality/ — AikoMind, catalog, adaptive memory"]
    Presentation["presentation/ — localized views and visual policies"]
    Widgets["ui/ — Tkinter character and windows"]
    Desktop["desktop/ — timers, input, native Windows adapters"]
    Infra["infrastructure/ — hardware and JSON storage"]
    Telemetry["telemetry.py — immutable measurement values"]
    Ports["application/ports.py — data/reading interfaces"]

    Shell --> App
    Shell --> Presentation
    Shell --> Widgets
    Shell --> Desktop
    Shell --> Infra
    App --> Domain
    App --> Mind
    App --> Ports
    Ports --> Telemetry
    Infra --> Telemetry
    Presentation --> App
    Presentation --> Domain
    Presentation --> Mind
    Widgets --> Presentation
    Desktop --> Widgets
    Infra -. "structurally satisfies reader ports" .-> Ports
```

The solid arrows highlight major code dependencies; the dotted provider-to-port
relationship represents structural compatibility, **not** an import from
infrastructure into the application. The checked-in tests enforce
additional import rules. Platform-level coordination intentionally happens
in the desktop shell; the architecture does not pretend to eliminate
all runtime coupling between composed services.

## State and business rules

**`pet/state.py — PetState`** is the only mutable, persisted pet aggregate. Its public `interact(action, now=...)` and `advance(now, ...)` operations commit care and elapsed-time state changes. Pure policy modules in `pet/` calculate immutable decisions:

- `care_actions.py`: `CareTransition` for care actions and their rewards.
- `need_decay.py`: `NeedLevels` for time and measured effort.
- `friendship.py`: relationship gains, cooldowns and daily limits.
- `lifecycle.py` and `routine.py`: bounded catch-up, sleep and daily schedule.

**`personality/mind.py — AikoMind`** selects reactions and maintains short-term conversational context. It does not display windows or speak through an audio device. `WorkloadEventDetector` in `personality/workload_events.py` converts observed load changes into event keys; The historical `ComputerVoice` alias has been removed. Authored dialogue is stored in `aiko_pet/data/dialogues.de.json`.

**`personality/adaptive.py`** learns coarse local daily patterns from observations. Unknown hardware readings do not become fabricated activity. No application names, process titles or content are collected for this version.

Some original domain convenience methods still return German text, such as `PetState.mood_hint()` and `TimeContext.greeting()`. They are retained for compatibility; **production status/hover copy** is formatted in `presentation/text_de.py`.

## Application layer

- `CareController.execute()` advances pet time, coordinates the character's care event, applies the command and returns a presentation-independent `CareOutcome`.
- `ApplicationRouter` accepts owner-thread care commands and validated, bounded incoming notifications. An external HTTP or IPC server is **not implemented**.
- `ActivityCoordinator` consumes hardware samples and coordinates adaptive observations and elapsed-time pet state.
- `AttentionCoordinator` controls spontaneous lines, non-interrupting notifications and idle gestures.
- `PetSessionRestorer` restores saved data through a narrow reader port and performs catch-up only for a valid existing save.
- `PetReadSnapshot` is an immutable, language-neutral copy for presentation and potential future read-only adapters.
- `application/ports.py` describes capabilities such as `ComputerReadings`, not concrete OS drivers.

The application never imports Tkinter or native system monitor implementations.

## Presentation and Tk widgets

`presentation/read_models.py` owns `DesktopPresentation`, converting pet read snapshots, typed settings and telemetry into immutable German `HoverSnapshot`, `StatusSnapshot` and `SettingsSnapshot` objects. `presentation/projections.py` formats display values; `presentation/text_de.py` owns German UI wording.

Concrete widgets belong under `ui/`:

- `AnimatedPet` draws Aiko and delegates animation-frame, gaze and walking calculations to pure presentation policies. Its cancellable frame timer honors individual image hold durations independently of the 140 ms simulation tick. Late callbacks show the next pose rather than skipping ahead, extending one-shot deadlines as needed. Walking positions update at most every 33 ms while simulation and hardware decisions retain their original tick. One-shot care actions return to idle; sleep plays the breathing loop.
- `HoverUi` controls the toolbar, status window and settings popup independently from the animated character.
- `SpeechPresenter` manages the existing speech/emote overlay.
- `ActionToolbar` owns one cohesive widget, including its six bars, buttons, drag handling and visibility lifecycle.

`presentation/reaction_playback.py` performs the timed emote → text → optional follow-up sequence with cancellation.

## Desktop runtime and operating-system adapters

`gui.DesktopPet` is the composition root. It constructs the single graph of application, UI, desktop services and providers, wires callbacks and starts `DesktopLifecycle`.

- `DesktopRuntime` takes explicit `DesktopTickPorts` and owns the ordered 140 ms update cycle and timer IDs.
- `DesktopPreferences` coordinates the consequences of option changes without a second settings model.
- `DesktopInput` owns Tk bindings, global click checks and cancellable delayed focus callbacks.
- `DesktopLifecycle` controls startup/shutdown ordering.
- `desktop/taskbar.py` and `window_stack.py` own Windows-specific taskbar discovery and z-order operations; `desktop/geometry.py` contains pure taskbar value calculations.

`infrastructure/character_assets.py` reads the prepared character catalog into immutable `presentation/character.py` contracts before Tk widgets are constructed. Full-width frames and visible ground anchors preserve the wider sleeping pose. `tools/prepare_character_assets.py` produces runtime PNGs with the existing Windows alpha threshold while retaining all source files in the separate asset bundle. Attack is cataloged but has no trigger. See [asset licensing](../ASSETS.md).

Hardware implementation details live in `infrastructure/hardware/`. `telemetry.ComputerSnapshot` is immutable and shared by the provider and application layers. The sampler uses local OS APIs and optional bounded NVIDIA tooling.

## Persistence, configuration and privacy

`infrastructure/persistence.py — StateStore` is the only implementation of the version-one atomic local JSON repository. The default Windows file is `%LOCALAPPDATA%\AikoDesktopPet\state.json`. The sole optional environment override, `AIKO_SAVE_PATH`, selects another **file path**. No `.env` is required.

- Storage decodes/writes data but does not simulate elapsed pet time.
- The application applies bounded restoration, need decay and saved-state advancement.
- Tests use temporary save files, never the user's production save.
- No cloud, login, browser integration, microphone listener or network service is started.

See [privacy and installation](../README.md#privacy-and-local-data) and [integration design](INTEGRATION_ARCHITECTURE.md) for future, explicitly unimplemented extension points.

## Import migration

The 2026-10-13 repository usage review found no runtime consumers of the 25
flat-module forwarding files or the five old application view modules.
Their imports were confined to tests and forwarding modules. `DesktopPet`
inherited `DesktopCompatibility`, but its live code already accessed the
owning components directly. `presentation/legacy.py` only supported the old
view modules and their tests. These 32 files have been removed, and the
behavior tests now exercise their canonical owners directly.

The source launchers (`main.py`, `Aiko_Pet.pyw`, `python -m aiko_pet` and both
Windows batch files) use `aiko_pet.gui.main` and require no import migration.
Version-one JSON saves, save-path configuration, sprites and authored dialogue
are unchanged. The repository review cannot establish whether unknown external
Python code imports the removed paths; such callers need the mappings below.

| Removed path under `aiko_pet` | Canonical owner |
| --- | --- |
| `domain` | `pet.state.PetState`; care/friendship/time constants and functions in their respective `pet` policy modules |
| `care_actions`, `friendship`, `need_decay`, `routine`, `value_rules` | Modules of the same name under `pet` |
| `pet_lifecycle` | `pet.lifecycle` |
| `adaptive`, `adaptive_models`, `adaptive_policy`, `work_episode`, `reaction_sequence` | Modules of the same name under `personality` |
| `dialogue` | `personality.mind.AikoMind` and `personality.catalog` types |
| `dialogue_catalog`, `dialogue_events` | `personality.catalog`, `personality.click_policy` |
| `computer_voice`; `ComputerVoice` alias | `personality.workload_events.WorkloadEventDetector` |
| `animation`, `gaze`, `movement`, `reaction_playback` | Modules of the same name under `presentation` |
| `desktop_input` | `desktop.global_input` |
| `taskbar` | `desktop.taskbar` and `desktop.geometry.TaskbarTrack` |
| `window_stack` | `desktop.window_stack` |
| `storage` | `infrastructure.persistence.StateStore`; settings in `application.settings` |
| `system_activity` | Providers in `infrastructure.hardware`; shared snapshots/effort in `telemetry` |
| `application.view_models` | `presentation.contracts` |
| `application.hover_projection`, `status_projection`, `settings_projection` | `presentation.projections` |
| `application.read_models`; `presentation.legacy.DesktopViewSource` | `presentation.read_models.DesktopPresentation` |
| `desktop.compatibility.DesktopCompatibility` | Owning `DesktopPet` components; no replacement facade |

Hover/status projectors accept `application.read_snapshot.snapshot_pet(state)`
instead of a mutable `PetState`. The status projector accepts the selected
emotion string rather than an `AikoMind` and timestamp. `DesktopPresentation`
provides desktop views without exposing the old public component handles.

Legacy desktop accesses such as `pet.toolbar`, `pet._bubble`, `pet.say()` and
`pet._walk_remaining` have been retired. Desktop composition and integration
tests use `pet._hover`, `pet._speech` and `pet._animated` respectively. These
are implementation components, not a new public integration API. Future
external adapters should use the typed application boundary.

Unused widget, asset and policy re-exports from `gui.py` have also been
removed; import them from `ui`, `asset_paths`, `presentation` or `desktop`.
The application uses `workload_events`, not the old `computer_voice` attribute.
Existing domain convenience methods and version-one data decoding remain
outside this module-import cleanup.

## Testing and contribution

GitHub Actions checks:

- Full Python 3.11 and 3.13 unit/Tk suites under Linux/Xvfb.
- Windows-hosted headless checks for native boundary logic.
- Ruff, PEP 8 line lengths, strict Mypy and Pyright.
- Domain invariants, immutable read data, import boundaries without legacy exceptions, and absence of module import cycles.

Native Windows layering, transparent-window and taskbar behavior must also be tested interactively for relevant changes. The October 2026 OOP refactor passed its full automated checks and received maintainer-reported Windows acceptance before [PR #2](https://github.com/Lexoniarus/aiko-desktop-pet/pull/2) merged.

For local commands, source changes and review expectations see [CONTRIBUTING.md](../CONTRIBUTING.md). Detailed refactor decisions are archived in [REFACTOR_ARCHITECTURE.md](REFACTOR_ARCHITECTURE.md) and the [dated architecture audit](ARCHITECTURE_AUDIT_20261013.md).
