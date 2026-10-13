# Aiko architecture audit — 2026-10-13

**Status:** Incremental refactor, not final Windows acceptance. Work is
isolated to `refactor/oop-modular-architecture`.

## Ownership and module boundaries

| Responsibility | Implemented owner |
| --- | --- |
| Domain state mutation owner | `pet/state.py` (`PetState`) |
| Pure care, needs, friendship and routine decisions | `pet/care_actions.py`, `pet/need_decay.py`, `pet/friendship.py`, `pet/lifecycle.py` |
| Care use-case coordination | `application/controller.py` |
| Incoming app/browser notifications | `application/router.py` and `inbox.py` |
| Comment timing, cursor/walk decisions and presentation interruption | `application/attention.py` |
| Workload, adaptive routine and pet time advancement | `application/activity.py` |
| Verified work episode/recovery memory for dialogue | `work_episode.py` |
| Semantic application read data | `application/read_snapshot.py` |
| Immutable German UI projection and geometry | `presentation/contracts.py`, `projections.py`, `read_models.py` |
| Hardware sample contract and provider capabilities | `telemetry.py`, `application/ports.py` |
| Animated character and walking | `ui/animated_pet.py` |
| Taskbar geometry and transparent root | `ui/desktop_window.py` |
| Hover, status and settings lifecycle | `ui/hover_ui.py` and UI views |
| Speech and ordered emotes | `ui/speech_presenter.py`, `reaction_playback.py` |
| Hover layout and drag rules | `ui/hover_geometry.py` |
| Legacy GUI method compatibility | `desktop/compatibility.py` |
| Tick timers and update phases | `desktop/runtime.py` (`DesktopTickPorts`) |
| Desktop preference effects | `desktop/preferences.py` |
| Save decoding and atomic JSON writes | `storage.py` |
| Runtime preferences and compatibility exports | `application/settings.py`, `storage.py` |
| Startup restoration and valid-save time catch-up | `application/session.py` |
| State serialization and autosave cadence | `desktop/persistence.py` |
| Taskbar/window stack checks | `desktop/maintenance.py` |
| Tk/global mouse and focus input | `desktop/input.py` (cancellable FocusOut) |
| Desktop startup/shutdown resource sequence | `desktop/lifecycle.py` |
| Hardware readings and effort | `infrastructure/hardware/metrics.py` |
| Windows/Linux OS sensors | `infrastructure/hardware/os_sensors.py` |
| NVIDIA discovery and CSV parsing | `infrastructure/hardware/nvidia.py` |
| CPU/GPU smoothing and bounded GPU call | `infrastructure/hardware/sampler.py` |
| Background worker and cached readings | `infrastructure/hardware/monitor.py` |
| Legacy sensor import compatibility | `system_activity.py` |
| Component composition and remaining GUI adapters | `gui.py` |

The original `gui.py` mixed all those responsibilities and measured 875
lines. The composition shell is now about 572 lines. The legacy
compatibility adapter still exists, but the active desktop scheduler no longer
calls its private forwarding methods. Timer ordering, persistence,
taskbar/stack checks, input and setting effects now have explicit owners.
Domain time advancement is owned by `ActivityCoordinator`, including
the pre-save catch-up.
Initial catch-up for an existing saved session is now performed by
`PetSessionRestorer` rather than `StateStore`; the repository performs only
JSON decoding/encoding and preserves legacy import names.
Startup and shutdown
are now ordered by `DesktopLifecycle` rather than duplicated in the
composition root.

## Dependency rule

    future authenticated integration adapter
                   |
                   v
       application commands / events
              |              |
           domain          immutable read contracts
              ^              |
              |              v
       local providers     UI presenters
                               |
                           Tk desktop

Application code must not import Tk or UI implementations. UI widgets
must not access `DesktopPet` or mutable game/persistence classes. The
animated character and native window now use structural typing protocols
instead of importing specific domain models. Old UI snapshot imports
re-export the exact application view-model classes.

Only the `gui.py` bootstrap connects these components. The shell now reads
the owned hover, animated character, speech, timing and taskbar components
directly instead of using inherited compatibility getters and presenters.
The compatibility adapter remains available to old callers. The runtime
receives typed, named `DesktopTickPorts` composed in `gui.py` instead of
using compatibility forwards as its tick stage surface. New features must
not depend on the old façade.

## Startup session ownership — implemented

`application/settings.py` owns `PetSettings` and `application/session.py`
owns `PetSessionRestorer` through the `SavedPetReader` port. `StateStore`
loads saved values without advancing them. Only valid prior saves are
advanced in the application. The existing JSON schema, defaults and
legacy import compatibility remain unchanged.

## Domain transition ownership — implemented

`PetState` now drives its own `interact()` and `advance()` operations,
using calculated `CareTransition`, `NeedLevels`, `FriendshipTransition`,
`RoutineTransition` and `SimulationStep` values. No policy calls private
methods of the aggregate to mutate it. Stateless domain decision modules
remain separately testable. Legacy module-level action and timeline APIs are
kept as compatibility adapters, without changing persistence schema.

A limited presentation concern remains: `PetState.mood_hint()` and
`PetState.feed_label()` provide German display copy. Relocate their
production use at the application/UI projection boundary in the next step,
while preserving public callers and dependency direction.

## Presentation boundary — implemented, with compatibility shims

The live desktop now uses `DesktopPresentation`, not the old application
view source. It snapshots `PetState` into `PetReadSnapshot` and formats
localized hover and status models in `presentation/`. `HoverAnchor` now
belongs to the presentation contracts. Hardware telemetry is an immutable
provider-neutral value in `telemetry.py`; application coordinators import
only structural hardware-reading ports. `SettingKey` is shared by the
settings UI and the desktop setting dispatcher.

The old `application.view_models` import path re-exports unchanged view
types, while the three old application projections remain callable as
legacy compatibility interfaces. The `PetState` and `TimeContext` German
helpers are retained for older callers but unused in live UI presentation.
Schedule descriptions embedded in `TimeContext` remain an identified
later compatibility cutover; their values were not changed here.

## Desktop runtime and preference ownership — implemented

The scheduler now owns only bounded time deltas, phase ordering and timer IDs.
Every dependency is exposed as a named `DesktopTickPorts` callback; it does
not accept the desktop shell or look up inherited private methods.
`DesktopPreferences` coordinates setting changes and position/scale
effects against their existing owners, rather than replicating state.
`DesktopInput` cancels delayed FocusOut callbacks on ordered shutdown.

The old `DesktopPet` façade remains intentionally inherited for legacy
consumers and tests; it does not drive normal runtime scheduling. Removing it
requires separate evidence that every existing entrypoint can be maintained.

## Canonical pet package — implemented

The `aiko_pet/pet/` package owns the sole PetState implementation and its
cohesive care, need, friendship, daily routine and value policies. Old
flat-module paths are thin re-export shims with exact type identity.
Application, presentation, storage and desktop consumers now import the
canonical state/routine modules. Tests forbid policy dependencies on
outer packages or independent legacy implementations.

## Remaining work, by priority (not yet implemented)

1. **Implemented:** timer scheduling, autosave, taskbar/stack inspection,
   mouse/focus binding and ordered desktop startup/shutdown. The lifecycle
   owns existing resources but contains no care/dialogue policy.
2. **Implemented:** the former 337-line `system_activity.py` is now
   only the compatibility façade. The implementation lives in
   `infrastructure/hardware/`, separated into immutable readings,
   Windows/Linux OS sensors, NVIDIA discovery/parsing, CPU/GPU sampling
   and the independent background monitor. Public imports are preserved.
3. **Implemented:** `dialogue.py` now delegates observed work episode
   transitions, counted interruptions, unusual workload classification and
   one-time recovery commentary to `work_episode.py`. `AikoMind` retains
   dialogue coordination, mood priorities, click/care selections and the
   separately testable spontaneous topic policy. No dialogue text was edited.
4. **In progress:** package the adaptive/dialogue and platform-native
   components by responsibility, retaining identical public imports and
   avoiding decorative folders.
5. Review remaining widget construction in the 320-line `action_toolbar.py`.
   Pure geometry was extracted; further splits require cohesive widgets.

Do not introduce a new HTTP server, AI backend or speculative event bus
as a prerequisite for the code-structure refactor.

## Regression barriers

- Ruff and E501 source checks, strict Mypy, project-wide Pyright.
- GUI tests on Python 3.11 and 3.13 under Linux/Xvfb.
- Windows-hosted headless tests and desktop module imports.
- AST architecture checks prevent application-to-UI and UI-to-domain
  reverse imports. Pure policy modules may not call aggregate-private
  mutators; the aggregate may not use mutable legacy adapters.
  `gui.py` still has an explicit 600-line limit.
- Manual real Windows tests remain a merge prerequisite.

**No merge, schema change, asset change or local save rewrite.**
